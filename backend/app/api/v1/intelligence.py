from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.models.models import (
    Profile, Project, Parcel, ProjectHealthScore, ParcelHealthScore,
    DataConflict, Escalation, Possession, Dependency, ResourcePriority,
)
from app.models.models import (
    ProjectHealthScore as PHS, ParcelHealthScore as ParHS,
)

router = APIRouter()


def _dict(obj, fields):
    out = {}
    for f in fields:
        v = getattr(obj, f, None)
        if isinstance(v, UUID):
            out[f] = str(v)
        else:
            out[f] = v
    return out


# --------------------------------------------------------------------------
# Project & parcel health
# --------------------------------------------------------------------------
@router.get("/health/projects")
async def list_project_health(
    band: str = Query(None),
    state_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(PHS, Project.project_code, Project.name, Project.status) \
        .join(Project, Project.id == PHS.project_id)
    if band:
        q = q.where(PHS.band == band)
    if state_id:
        q = q.where(Project.state_id == state_id)
    rows = (await db.execute(q)).all()
    data = []
    for hv, code, name, status in rows:
        data.append({
            "id": str(hv.id), "project_id": str(hv.project_id),
            "project_code": code, "project_name": name, "project_status": status,
            "score": hv.score, "band": hv.band, "factors": hv.factors,
            "computed_at": hv.computed_at.isoformat() if hv.computed_at else None,
        })
    return {"success": True, "data": data, "total": len(data), "message": "Health scores retrieved"}


@router.get("/health/projects/{project_id}")
async def get_project_health(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    hv = (await db.execute(select(PHS).where(PHS.project_id == project_id))).scalars().first()
    if not hv:
        raise HTTPException(status_code=404, detail="No health record for project")
    return {"success": True, "data": _dict(hv, ["id", "project_id", "score", "band", "factors", "computed_at"]),
            "message": "Health score retrieved"}


@router.get("/health/parcels")
async def list_parcel_health(
    band: str = Query(None),
    project_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(ParHS, Parcel.parcel_code, Parcel.current_status) \
        .join(Parcel, Parcel.id == ParHS.parcel_id)
    if band:
        q = q.where(ParHS.band == band)
    if project_id:
        q = q.where(ParHS.project_id == project_id)
    rows = (await db.execute(q)).all()
    data = [{"id": str(hv.id), "parcel_id": str(hv.parcel_id), "parcel_code": code,
             "parcel_status": status, "score": hv.score, "band": hv.band,
             "factors": hv.factors, "computed_at": hv.computed_at.isoformat() if hv.computed_at else None}
            for hv, code, status in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Parcel health retrieved"}


@router.get("/health/parcels/{parcel_id}")
async def get_parcel_health(
    parcel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    hv = (await db.execute(select(ParHS).where(ParHS.parcel_id == parcel_id))).scalars().first()
    if not hv:
        raise HTTPException(status_code=404, detail="No health record for parcel")
    return {"success": True, "data": _dict(hv, ["id", "parcel_id", "project_id", "score", "band", "factors", "computed_at"]),
            "message": "Parcel health retrieved"}


# --------------------------------------------------------------------------
# Data conflicts
# --------------------------------------------------------------------------
@router.get("/conflicts")
async def list_conflicts(
    severity: str = Query(None),
    status: str = Query(None),
    project_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(DataConflict).order_by(DataConflict.detected_at.desc())
    if severity:
        q = q.where(DataConflict.severity == severity)
    if status:
        q = q.where(DataConflict.status == status)
    if project_id:
        q = q.where(DataConflict.project_id == project_id)
    rows = (await db.execute(q)).scalars().all()
    data = [_dict(r, ["id", "conflict_code", "project_id", "parcel_id", "source_a", "source_b",
                      "field_name", "old_value", "new_value", "severity", "status",
                      "resolution_reason", "detected_at", "resolved_at", "evidence"]) for r in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Conflicts retrieved"}


@router.get("/conflicts/{conflict_id}")
async def get_conflict(
    conflict_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    c = (await db.execute(select(DataConflict).where(DataConflict.id == conflict_id))).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conflict not found")
    data = _dict(c, ["id", "conflict_code", "project_id", "parcel_id", "source_a", "source_b",
                     "field_name", "old_value", "new_value", "severity", "status",
                     "resolution_reason", "resolved_by", "detected_at", "resolved_at", "evidence"])
    data["project"] = {"id": str(c.project_id)}
    return {"success": True, "data": data, "message": "Conflict retrieved"}


# --------------------------------------------------------------------------
# Escalations
# --------------------------------------------------------------------------
@router.get("/escalations")
async def list_escalations(
    level: int = Query(None),
    status: str = Query(None),
    project_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(Escalation, Project.project_code, Project.name).join(Project, Project.id == Escalation.project_id)
    if level:
        q = q.where(Escalation.level == level)
    if status:
        q = q.where(Escalation.status == status)
    if project_id:
        q = q.where(Escalation.project_id == project_id)
    rows = (await db.execute(q.order_by(Escalation.level.desc()))).all()
    data = [{"id": str(e.id), "escalation_code": e.escalation_code, "project_id": str(e.project_id),
             "project_code": code, "project_name": name, "stage": e.stage,
             "trigger_reason": e.trigger_reason, "level": e.level,
             "responsible_authority": e.responsible_authority, "status": e.status,
             "created_date": e.created_date.isoformat() if e.created_date else None,
             "resolution_date": e.resolution_date.isoformat() if e.resolution_date else None,
             "resolution_action": e.resolution_action}
            for e, code, name in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Escalations retrieved"}


# --------------------------------------------------------------------------
# Possession
# --------------------------------------------------------------------------
@router.get("/possessions")
async def list_possessions(
    status: str = Query(None),
    project_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(Possession, Project.project_code, Parcel.parcel_code) \
        .join(Project, Project.id == Possession.project_id) \
        .join(Parcel, Parcel.id == Possession.parcel_id)
    if status:
        q = q.where(Possession.possession_status == status)
    if project_id:
        q = q.where(Possession.project_id == project_id)
    rows = (await db.execute(q)).all()
    data = [{"id": str(p.id), "project_id": str(p.project_id), "project_code": pcode,
             "parcel_id": str(p.parcel_id), "parcel_code": pcode2, "award_reference": p.award_reference,
             "possession_status": p.possession_status,
             "possession_date": p.possession_date.isoformat() if p.possession_date else None,
             "pending_reason": p.pending_reason, "verification_status": p.verification_status,
             "responsible_authority": p.responsible_authority}
            for p, pcode, pcode2 in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Possessions retrieved"}


# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------
@router.get("/dependencies")
async def list_dependencies(
    project_id: UUID = Query(None),
    dependency_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(Dependency, Project.project_code, Project.name).join(Project, Project.id == Dependency.project_id)
    if project_id:
        q = q.where(Dependency.project_id == project_id)
    if dependency_type:
        q = q.where(Dependency.dependency_type == dependency_type)
    rows = (await db.execute(q)).all()
    data = [{"id": str(d.id), "project_id": str(d.project_id), "project_code": code, "project_name": name,
             "from_stage": d.from_stage, "to_stage": d.to_stage, "dependency_type": d.dependency_type,
             "dependency_description": d.dependency_description, "is_satisfied": d.is_satisfied}
            for d, code, name in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Dependencies retrieved"}


# --------------------------------------------------------------------------
# Resource priorities
# --------------------------------------------------------------------------
@router.get("/priorities")
async def list_priorities(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(ResourcePriority, Project.project_code, Project.name, Project.status) \
        .join(Project, Project.id == ResourcePriority.project_id) \
        .order_by(ResourcePriority.priority_rank)
    rows = (await db.execute(q)).all()
    data = [{"id": str(r.id), "project_id": str(r.project_id), "project_code": code,
             "project_name": name, "project_status": status, "priority_score": r.priority_score,
             "priority_rank": r.priority_rank, "reasoning": r.reasoning,
             "update_date": r.update_date.isoformat() if r.update_date else None}
            for r, code, name, status in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Priorities retrieved"}
