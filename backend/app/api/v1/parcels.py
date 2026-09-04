from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import parcel_service
from app.schemas.parcel import ParcelCreate, ParcelUpdate, ParcelOwnerCreate
from app.models.models import Profile

router = APIRouter()


@router.get("")
async def list_parcels(
    state_id: UUID = Query(None),
    district_id: UUID = Query(None),
    tehsil_id: UUID = Query(None),
    village_id: UUID = Query(None),
    land_type: str = Query(None),
    ownership_type: str = Query(None),
    current_status: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await parcel_service.list_parcels(
        db=db, state_id=state_id, district_id=district_id,
        tehsil_id=tehsil_id, village_id=village_id,
        land_type=land_type, ownership_type=ownership_type,
        current_status=current_status, search=search,
        page=page, page_size=page_size,
    )
    data = [_parcel_to_dict(p) for p in result["data"]]
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Parcels retrieved",
    }


@router.post("", status_code=201)
async def create_parcel(
    data: ParcelCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    parcel = await parcel_service.create_parcel(
        db, data, current_user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "data": _parcel_to_dict(parcel),
        "message": "Parcel created successfully",
    }


@router.get("/{parcel_id}")
async def get_parcel(
    parcel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    parcel = await parcel_service.get_parcel(db, parcel_id)
    return {
        "success": True,
        "data": _parcel_to_dict(parcel),
        "message": "Parcel retrieved",
    }


@router.put("/{parcel_id}")
async def update_parcel(
    parcel_id: UUID,
    data: ParcelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    parcel = await parcel_service.update_parcel(
        db, parcel_id, data, current_user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "data": _parcel_to_dict(parcel),
        "message": "Parcel updated successfully",
    }


@router.post("/{parcel_id}/owners", status_code=201)
async def add_owner(
    parcel_id: UUID,
    data: ParcelOwnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    owner = await parcel_service.add_owner(db, parcel_id, data, current_user)
    return {
        "success": True,
        "data": {
            "id": str(owner.id),
            "parcel_id": str(owner.parcel_id),
            "owner_name": owner.owner_name,
            "father_husband_name": owner.father_husband_name,
            "gender": owner.gender,
            "age": owner.age,
            "aadhaar_last4": owner.aadhaar_last4,
            "relation_to_holder": owner.relation_to_holder,
            "is_primary": owner.is_primary,
            "contact_phone": owner.contact_phone,
            "address": owner.address,
        },
        "message": "Owner added successfully",
    }


def _parcel_to_dict(p):
    return {
        "id": str(p.id),
        "parcel_code": p.parcel_code,
        "survey_number": p.survey_number,
        "khasra_number": p.khasra_number,
        "ulpin": p.ulpin,
        "village_id": str(p.village_id),
        "tehsil_id": str(p.tehsil_id),
        "district_id": str(p.district_id),
        "state_id": str(p.state_id),
        "land_type": p.land_type,
        "ownership_type": p.ownership_type,
        "area_sq_m": float(p.area_sq_m) if p.area_sq_m else None,
        "geometry": p.geometry,
        "current_status": p.current_status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "owners": [
            {
                "id": str(o.id),
                "owner_name": o.owner_name,
                "father_husband_name": o.father_husband_name,
                "gender": o.gender,
                "age": o.age,
                "aadhaar_last4": o.aadhaar_last4,
                "is_primary": o.is_primary,
                "contact_phone": o.contact_phone,
            }
            for o in (p.owners or [])
        ],
    }
