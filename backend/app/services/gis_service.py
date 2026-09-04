from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.models import GISVerification, Parcel, Project, ProjectParcel, AuditLog
from app.gis.spatial_ops import (
    calculate_area_from_geojson,
    check_geometry_validity,
    check_parcel_overlap,
    area_match_percentage,
)
from app.audit.service import log_action


async def verify_parcel(
    db: AsyncSession,
    project_id: UUID,
    parcel_id: UUID,
    officer_id: UUID,
    notes: Optional[str] = None,
) -> GISVerification:
    result = await db.execute(select(Parcel).where(Parcel.id == parcel_id))
    parcel = result.scalar_one_or_none()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    result = await db.execute(
        select(ProjectParcel).where(
            ProjectParcel.project_id == project_id,
            ProjectParcel.parcel_id == parcel_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=400,
            detail="Parcel is not part of this project",
        )

    geometry = parcel.geometry
    geometry_valid = check_geometry_validity(geometry) if geometry else False
    area_ok = area_match_percentage(float(parcel.area_sq_m), geometry) if geometry else False

    overlap_detected = False
    overlap_parcel_ids = []
    conflict_details = {}

    if geometry:
        result = await db.execute(
            select(Parcel).where(
                Parcel.id != parcel.id,
                Parcel.geometry.isnot(None)
            )
        )
        all_parcels = result.scalars().all()
        overlaps = []
        for other in all_parcels:
            if other.geometry:
                if check_parcel_overlap(geometry, other.geometry):
                    overlaps.append(str(other.id))
                    overlap_detected = True
        overlap_parcel_ids = overlaps
        conflict_details = {
            "overlapping_parcels": overlaps,
            "message": "Overlap detected with adjacent parcels" if overlap_detected else "No overlap detected",
        }

    verification = GISVerification(
        project_id=project_id,
        parcel_id=parcel_id,
        verified_by=officer_id,
        geometry_valid=geometry_valid,
        area_match=area_ok,
        overlap_detected=overlap_detected,
        overlap_parcel_ids=overlap_parcel_ids,
        outside_boundary=False,
        conflict_details=conflict_details,
        verification_notes=notes,
    )
    db.add(verification)
    await db.flush()

    await log_action(
        db=db, actor_id=officer_id, actor_email=None,
        action="GIS_VERIFICATION", entity_type="parcel", entity_id=parcel_id,
        new_value={
            "geometry_valid": geometry_valid,
            "area_match": area_ok,
            "overlap_detected": overlap_detected,
        },
    )
    return verification


async def get_project_verifications(db: AsyncSession, project_id: UUID) -> list:
    result = await db.execute(
        select(GISVerification)
        .where(GISVerification.project_id == project_id)
        .order_by(GISVerification.verified_at)
    )
    return result.scalars().all()


async def check_overlap(
    db: AsyncSession,
    parcel_id: UUID,
    geometry: dict,
    excluded_id: Optional[UUID] = None,
) -> dict:
    result = await db.execute(
        select(Parcel).where(
            Parcel.geometry.isnot(None)
        )
    )
    all_parcels = result.scalars().all()

    if geometry is None:
        return {
            "overlap_detected": False,
            "overlapping_parcels": [],
            "message": "No geometry provided",
        }

    overlaps = []
    for other in all_parcels:
        if excluded_id and other.id == excluded_id:
            continue
        if other.geometry and check_parcel_overlap(geometry, other.geometry):
            overlaps.append(str(other.id))

    return {
        "overlap_detected": len(overlaps) > 0,
        "overlapping_parcels": overlaps,
        "message": f"Overlap detected with {len(overlaps)} parcel(s)" if overlaps else "No overlap detected",
    }
