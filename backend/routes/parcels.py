"""GIS cadastral vector layer.

Serves parcel polygons straight out of PostGIS as a GeoJSON FeatureCollection,
which is the shape the Leaflet client consumes directly.

Authorisation is enforced by :func:`require_auth`, not by Row Level Security.
The backend holds Supabase's `service_role` key, which bypasses RLS, so the API
layer is the only thing standing between the database and an anonymous caller.
Adding `dependencies=[Depends(require_auth)]` is therefore mandatory on every
route in this file -- omitting it would expose land records publicly.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
try:  # package-relative: `python -m backend.main`
    from ..database import get_supabase
    from ..security import require_auth
except ImportError:  # flat layout: `uvicorn main:app` from inside backend/
    from database import get_supabase
    from security import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/parcels",
    tags=["Parcels"],
    dependencies=[Depends(require_auth)],
)

# The parcel_status enum. Validated before it reaches the database so an
# unknown status is a clean 422 instead of a Postgres cast error surfacing as 500.
VALID_STATUSES = {
    "ACQUIRED",
    "UNDER_PROCESS",
    "COMP_PENDING",
    "POSSESSION_PENDING",
    "RR_PENDING",
    "HIGH_RISK",
}

# user_role enum. A token carrying anything outside this set resolves to
# no rows instead of failing the cast inside Postgres.
VALID_ROLES = {
    "CENTRAL",
    "STATE",
    "DISTRICT",
    "AGENCY",
    "FIELD_OFFICER",
}

# NOTE ON JURISDICTION FIELDS
# The frontend parcel detail panel reads `properties.state` and
# `properties.district`, but neither exists anywhere in this schema: `land_parcels`
# and `projects` carry no geography columns, and only `profiles` has state/district
# (the caller's own posting, not the parcel's).
#
# These values are therefore deliberately NOT synthesised here. Deriving a state
# from a `project_code` prefix would have invented data for every code outside that
# guess, which is worse than an absent field: a missing value renders as "unknown",
# whereas a wrong one silently misstates where land is being acquired. `state` and
# `district` are populated only in the demo fixture. Adding them to the live path
# requires real columns (or a state/district reference table) -- see the schema
# gap called out in the handover notes.


def _empty_collection() -> dict:
    """A valid, empty FeatureCollection.

    Returning this for "no rows" (rather than null) keeps the response schema
    stable, so the client never has to special-case an empty project.
    """
    return {"type": "FeatureCollection", "features": []}


def _validate_status(status_filter: str | None) -> str | None:
    if not status_filter:
        return None
    candidate = status_filter.strip().upper()
    if candidate not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown status '{status_filter}'. Expected one of: "
            + ", ".join(sorted(VALID_STATUSES)),
        )
    return candidate


@router.get("/geojson")
def parcels_geojson(
    project_code: str | None = None,
    status: str | None = None,
    principal: dict = Depends(require_auth),
):
    """Return parcel polygons as a GeoJSON FeatureCollection.

    Query parameters:
        project_code: optional project filter, e.g. ``PRJ-PRY-001``
        status: optional `parcel_status` filter

    The caller's identity is forwarded into the SQL function, which re-applies
    the `parcels_select` rule. That is required because this service talks to
    PostgREST with the `service_role` key, which bypasses Row Level Security --
    without the explicit scope below, every officer would receive every parcel.
    """
    clean_status = _validate_status(status)

    # `sub` is the Supabase Auth user id, which is what `land_parcels.created_by`
    # references. A malformed claim yields no rows rather than an error.
    try:
        caller_id = uuid.UUID(principal["sub"])
    except (KeyError, TypeError, ValueError):
        caller_id = None

    caller_role = principal.get("role")

    try:
        response = (
            get_supabase()
            .rpc(
                "parcels_geojson",
                {
                    "p_project_code": project_code or None,
                    "p_status": clean_status,
                    "p_user_id": str(caller_id) if caller_id else None,
                    "p_role": caller_role if caller_role in VALID_ROLES else None,
                },
            )
            .execute()
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Parcel GeoJSON query failed")
        raise HTTPException(
            status_code=502,
            detail="Parcel data is currently unavailable. Please retry.",
        )

    collection = response.data
    if not isinstance(collection, dict):
        # PostgREST returns a scalar jsonb column as an already-parsed object.
        # Anything else means the function did not run as expected.
        logger.warning("parcels_geojson returned unexpected shape: %r", type(collection))
        return _empty_collection()

    features = collection.get("features")
    if not isinstance(features, list):
        return _empty_collection()

    return collection
