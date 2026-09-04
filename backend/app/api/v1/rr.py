from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import rr_service
from app.schemas.rr import RRCaseCreate, RRCaseUpdate
from app.models.models import Profile

router = APIRouter()


@router.get("")
async def list_rr_cases(
    project_id: UUID = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await rr_service.list_rr_cases(
        db=db, project_id=project_id, status_filter=status,
        page=page, page_size=page_size,
    )
    data = [_rr_to_dict(c) for c in result["data"]]
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "RR cases retrieved",
    }


@router.post("", status_code=201)
async def create_rr_case(
    data: RRCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await rr_service.create_rr_case(db, data, current_user)
    return {
        "success": True,
        "data": _rr_to_dict(case),
        "message": "RR case created",
    }


@router.get("/{case_id}")
async def get_rr_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await rr_service.get_rr_case(db, case_id)
    return {
        "success": True,
        "data": _rr_to_dict(case),
        "message": "RR case retrieved",
    }


@router.put("/{case_id}")
async def update_rr_case(
    case_id: UUID,
    data: RRCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await rr_service.update_rr_case(db, case_id, data, current_user)
    return {
        "success": True,
        "data": _rr_to_dict(case),
        "message": "RR case updated",
    }


def _rr_to_dict(c):
    return {
        "id": str(c.id),
        "project_id": str(c.project_id),
        "parcel_id": str(c.parcel_id),
        "landowner_id": str(c.landowner_id),
        "family_members_count": c.family_members_count,
        "eligibility_status": c.eligibility_status,
        "entitlement_details": c.entitlement_details,
        "assistance_type": c.assistance_type,
        "assigned_officer_id": str(c.assigned_officer_id) if c.assigned_officer_id else None,
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }
