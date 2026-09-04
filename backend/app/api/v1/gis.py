from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import gis_service
from app.models.models import Profile, Parcel
from app.schemas.gis import GISOverlapCheckRequest

router = APIRouter()


@router.post("/verify/{project_id}/{parcel_id}")
async def verify_parcel_gis(
    project_id: UUID,
    parcel_id: UUID,
    notes: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    verification = await gis_service.verify_parcel(
        db, project_id, parcel_id, current_user.id, notes
    )
    return {
        "success": True,
        "data": {
            "id": str(verification.id),
            "project_id": str(verification.project_id),
            "parcel_id": str(verification.parcel_id),
            "geometry_valid": verification.geometry_valid,
            "area_match": verification.area_match,
            "overlap_detected": verification.overlap_detected,
            "overlap_parcel_ids": verification.overlap_parcel_ids,
            "outside_boundary": verification.outside_boundary,
            "verification_notes": verification.verification_notes,
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
        },
        "message": "GIS verification completed",
    }


@router.get("/project/{project_id}/verifications")
async def get_project_verifications(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    verifications = await gis_service.get_project_verifications(db, project_id)
    return {
        "success": True,
        "data": [
            {
                "id": str(v.id),
                "project_id": str(v.project_id),
                "parcel_id": str(v.parcel_id),
                "verified_by": str(v.verified_by) if v.verified_by else None,
                "geometry_valid": v.geometry_valid,
                "area_match": v.area_match,
                "overlap_detected": v.overlap_detected,
                "overlap_parcel_ids": v.overlap_parcel_ids,
                "verification_notes": v.verification_notes,
                "verified_at": v.verified_at.isoformat() if v.verified_at else None,
            }
            for v in verifications
        ],
        "message": "GIS verifications retrieved",
    }


@router.post("/check-overlap")
async def check_overlap(
    data: GISOverlapCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await gis_service.check_overlap(
        db, data.parcel_id, data.geometry
    )
    return {
        "success": True,
        "data": result,
        "message": result["message"],
    }
