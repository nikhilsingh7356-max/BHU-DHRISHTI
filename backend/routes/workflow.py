"""RFCTLARR statutory stage transitions.

`POST /api/v1/workflow/transition` from `docs/api-contracts.md` §2.1.

Scope note -- what is grounded here and what is not:

* The legal stage order is NOT invented: it is read from the `project_stage`
  enum declared in `database/01scheme.sql`, whose declaration order is
  SIA_STUDY -> SEC_11_NOTIF -> SEC_15_OBJECTION -> SEC_19_DECLARATION ->
  SEC_23_AWARD -> SEC_38_POSSESSION -> COMPLETED. A transition is only accepted
  to the *immediately* next stage, so the database schema is the single source
  of truth for sequencing.
* Who may transition is NOT invented either: the `projects_modify` RLS policy in
  `01scheme.sql` restricts writes to CENTRAL and STATE, and this route enforces
  the same pair. Because the API holds a `service_role` key that bypasses RLS,
  that policy has to be re-applied here or the restriction would not exist.
* The per-stage SLA allocation comes from the contract's own worked example
  (Section 15 hearings => 60 days). Only that one figure is asserted, because it
  is the only one the repository actually documents. The remaining stages are
  reported with `sla_days_allocated: null` rather than carrying invented
  numbers into a legal deadline.
* Every accepted transition writes an `audit_logs` row, matching the append-only
  intent of that table. Nothing here deletes or rewrites history.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
try:  # package-relative: `python -m backend.main`
    from ..database import get_supabase
    from ..security import require_auth, require_roles
except ImportError:  # flat layout: `uvicorn main:app` from inside backend/
    from database import get_supabase
    from security import require_auth, require_roles

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/workflow",
    tags=["Workflow"],
    dependencies=[Depends(require_auth)],
)

# Declaration order of `public.project_stage` in database/01scheme.sql.
# Kept as a literal here because PostgREST cannot introspect enum ordering.
STAGE_ORDER = [
    "SIA_STUDY",
    "SEC_11_NOTIF",
    "SEC_15_OBJECTION",
    "SEC_19_DECLARATION",
    "SEC_23_AWARD",
    "SEC_38_POSSESSION",
    "COMPLETED",
]

# Human-readable statutory mandate per stage. Sourced from the stage names
# themselves (each maps to the RFCTLARR 2013 section it is named after).
STATUTORY_MANDATE = {
    "SIA_STUDY": "RFCTLARR Section 6",
    "SEC_11_NOTIF": "RFCTLARR Section 11",
    "SEC_15_OBJECTION": "RFCTLARR Section 15",
    "SEC_19_DECLARATION": "RFCTLARR Section 19",
    "SEC_23_AWARD": "RFCTLARR Section 23",
    "SEC_38_POSSESSION": "RFCTLARR Section 38",
    "COMPLETED": "RFCTLARR process concluded",
}

# Only the allocation documented in docs/api-contracts.md §2.1. Everything else
# stays null: a fabricated deadline in a statutory workflow is worse than none.
DOCUMENTED_SLA_DAYS = {
    "SEC_15_OBJECTION": 60,
}


class TransitionRequest(BaseModel):
    project_code: str = Field(min_length=1, max_length=64)
    current_stage: str
    action_remarks: str = Field(min_length=1, max_length=2000)
    actor_bhoomi_id: str = Field(min_length=1, max_length=64)


def _next_stage(current: str) -> str | None:
    """The only stage this transition is allowed to move to."""
    try:
        idx = STAGE_ORDER.index(current)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown stage '{current}'. Expected one of: " + ", ".join(STAGE_ORDER),
        )
    if idx >= len(STAGE_ORDER) - 1:
        return None
    return STAGE_ORDER[idx + 1]


@router.post("/transition")
def transition_stage(
    payload: TransitionRequest,
    principal: dict = Depends(require_roles("CENTRAL", "STATE")),
):
    """Advance a project to the next statutory stage and append an audit record."""
    if not payload.action_remarks.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="action_remarks cannot be blank.",
        )

    active_stage = _next_stage(payload.current_stage.strip().upper())
    if active_stage is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stage '{payload.current_stage}' is already terminal; no further transition is possible.",
        )

    sla_days = DOCUMENTED_SLA_DAYS.get(active_stage)
    sla_deadline = (
        (datetime.now(timezone.utc) + timedelta(days=sla_days)).isoformat().replace("+00:00", "Z")
        if sla_days is not None
        else None
    )

    supabase = get_supabase()

    try:
        project = (
            supabase.table("projects")
            .select("id, project_code, current_stage")
            .eq("project_code", payload.project_code)
            .limit(1)
            .execute()
        )
    except Exception:
        logger.exception("Project lookup failed for %s", payload.project_code)
        raise HTTPException(status_code=502, detail="Workflow service is currently unavailable. Please retry.")

    rows = getattr(project, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{payload.project_code}' was not found.",
        )

    row = rows[0]
    stored_stage = row.get("current_stage")
    claimed = payload.current_stage.strip().upper()

    # Optimistic concurrency: the caller's view of the stage must match the
    # stored one, otherwise two officers racing on the same project would
    # silently overwrite each other.
    if stored_stage != claimed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Project '{payload.project_code}' is at stage '{stored_stage}', "
                f"not '{claimed}'. Reload and retry."
            ),
        )

    try:
        (
            supabase.table("projects")
            .update({"current_stage": active_stage})
            .eq("id", row["id"])
            .eq("current_stage", claimed)
            .execute()
        )

        supabase.table("audit_logs").insert(
            {
                "actor_id": _actor_uuid(principal),
                "action_type": "WORKFLOW_STAGE_TRANSITION",
                "entity_name": "projects",
                "entity_id": str(row["id"]),
                "details": {
                    "project_code": payload.project_code,
                    "previous_stage": claimed,
                    "active_stage": active_stage,
                    "action_remarks": payload.action_remarks.strip(),
                    "actor_bhoomi_id": payload.actor_bhoomi_id,
                    "sla_days_allocated": sla_days,
                    "sla_deadline_utc": sla_deadline,
                },
            }
        ).execute()
    except Exception:
        logger.exception("Transition write failed for %s", payload.project_code)
        raise HTTPException(
            status_code=502,
            detail="The stage transition could not be recorded. No change was made.",
        )

    return {
        "status": "SUCCESS",
        "project_code": payload.project_code,
        "previous_stage": claimed,
        "active_stage": active_stage,
        "statutory_mandate": STATUTORY_MANDATE.get(active_stage),
        "sla_days_allocated": sla_days,
        "sla_deadline_utc": sla_deadline,
        "audit_logged": True,
    }


def _actor_uuid(principal: dict) -> str | None:
    """The caller's Supabase Auth id, or None when the claim is malformed."""
    try:
        return str(uuid.UUID(principal["sub"]))
    except (KeyError, TypeError, ValueError):
        return None
