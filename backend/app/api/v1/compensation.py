from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import compensation_service
from app.schemas.compensation import CompensationCreate, CompensationUpdate, PaymentCreate
from app.models.models import Profile

router = APIRouter()


@router.get("")
async def list_compensation(
    project_id: UUID = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await compensation_service.list_compensation_cases(
        db=db, project_id=project_id, status_filter=status,
        page=page, page_size=page_size,
    )
    data = [_case_to_dict(c) for c in result["data"]]
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Compensation cases retrieved",
    }


@router.post("", status_code=201)
async def create_compensation(
    data: CompensationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await compensation_service.create_compensation_case(
        db, data.parcel_id, data.project_id, data.landowner_id, data, current_user
    )
    return {
        "success": True,
        "data": _case_to_dict(case),
        "message": "Compensation case created",
    }


@router.get("/{case_id}")
async def get_compensation(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await compensation_service.get_compensation_case(db, case_id)
    return {
        "success": True,
        "data": _case_to_dict(case),
        "message": "Compensation case retrieved",
    }


@router.put("/{case_id}")
async def update_compensation(
    case_id: UUID,
    data: CompensationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await compensation_service.update_compensation_case(db, case_id, data, current_user)
    return {
        "success": True,
        "data": _case_to_dict(case),
        "message": "Compensation case updated",
    }


@router.post("/{case_id}/approve")
async def approve_compensation(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    case = await compensation_service.approve_compensation(db, case_id, current_user)
    return {
        "success": True,
        "data": _case_to_dict(case),
        "message": "Compensation case approved",
    }


@router.post("/{case_id}/payments", status_code=201)
async def record_payment(
    case_id: UUID,
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    payment = await compensation_service.process_payment(
        db, case_id, data.amount, data.payment_method,
        data.payment_reference, data.payment_date, current_user,
    )
    return {
        "success": True,
        "data": {
            "id": str(payment.id),
            "case_id": str(payment.case_id),
            "amount": float(payment.amount),
            "payment_method": payment.payment_method,
            "payment_reference": payment.payment_reference,
            "payment_date": payment.payment_date.isoformat(),
            "status": payment.status,
        },
        "message": "Payment recorded",
    }


def _case_to_dict(c):
    return {
        "id": str(c.id),
        "parcel_id": str(c.parcel_id),
        "project_id": str(c.project_id),
        "landowner_id": str(c.landowner_id),
        "assessed_value": float(c.assessed_value) if c.assessed_value else None,
        "land_area_sq_m": float(c.land_area_sq_m) if c.land_area_sq_m else None,
        "compensation_components": c.compensation_components,
        "total_amount": float(c.total_amount) if c.total_amount else None,
        "status": c.status,
        "assigned_officer_id": str(c.assigned_officer_id) if c.assigned_officer_id else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }
