from datetime import datetime
from uuid import UUID
from typing import Optional, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.models import (
    CompensationCase, CompensationPayment, Parcel, ParcelOwner, Project, Profile
)
from app.audit.service import log_action
from app.notifications.service import create_notification


async def create_compensation_case(
    db: AsyncSession,
    parcel_id: UUID,
    project_id: UUID,
    landowner_id: UUID,
    data,
    user: Profile,
) -> CompensationCase:
    result = await db.execute(select(Parcel).where(Parcel.id == parcel_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    result = await db.execute(select(Project).where(Project.id == project_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await db.execute(select(ParcelOwner).where(ParcelOwner.id == landowner_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Landowner not found")

    case = CompensationCase(
        parcel_id=parcel_id,
        project_id=project_id,
        landowner_id=landowner_id,
        assessed_value=data.assessed_value,
        land_area_sq_m=data.land_area_sq_m,
        compensation_components=data.compensation_components,
        total_amount=data.total_amount,
        status="ASSESSED",
        assigned_officer_id=data.assigned_officer_id,
    )
    db.add(case)
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="CREATE_COMPENSATION_CASE", entity_type="compensation_case",
        entity_id=case.id,
        new_value={
            "parcel_id": str(parcel_id),
            "total_amount": str(data.total_amount) if data.total_amount else None,
        },
    )
    return case


async def list_compensation_cases(
    db: AsyncSession,
    project_id: UUID = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(CompensationCase)
    count_query = select(func.count(CompensationCase.id))
    if project_id:
        query = query.where(CompensationCase.project_id == project_id)
        count_query = count_query.where(CompensationCase.project_id == project_id)
    if status_filter:
        query = query.where(CompensationCase.status == status_filter)
        count_query = count_query.where(CompensationCase.status == status_filter)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(CompensationCase.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    cases = result.scalars().all()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "data": cases, "total": total, "page": page,
        "page_size": page_size, "total_pages": total_pages,
    }


async def get_compensation_case(db: AsyncSession, case_id: UUID) -> CompensationCase:
    result = await db.execute(
        select(CompensationCase)
        .where(CompensationCase.id == case_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail="Compensation case not found")
    return case


async def update_compensation_case(
    db: AsyncSession, case_id: UUID, data, user: Profile,
) -> CompensationCase:
    case = await get_compensation_case(db, case_id)
    if data.assessed_value is not None:
        case.assessed_value = data.assessed_value
    if data.land_area_sq_m is not None:
        case.land_area_sq_m = data.land_area_sq_m
    if data.compensation_components is not None:
        case.compensation_components = data.compensation_components
    if data.total_amount is not None:
        case.total_amount = data.total_amount
    if data.status is not None:
        case.status = data.status
    if data.assigned_officer_id is not None:
        case.assigned_officer_id = data.assigned_officer_id
    case.updated_at = datetime.utcnow()
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="UPDATE_COMPENSATION_CASE", entity_type="compensation_case",
        entity_id=case.id, new_value={"status": case.status},
    )
    return case


async def approve_compensation(db: AsyncSession, case_id: UUID, officer: Profile) -> CompensationCase:
    case = await get_compensation_case(db, case_id)
    if case.status not in ("ASSESSED", "PENDING_APPROVAL"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve case in status {case.status}",
        )
    case.status = "APPROVED"
    case.assigned_officer_id = officer.id
    case.updated_at = datetime.utcnow()
    await db.flush()

    await create_notification(
        db=db, user_id=None, title="Compensation Approved",
        message=f"Compensation case {case_id} has been approved",
        notification_type="STATUS_CHANGE",
        entity_type="compensation_case", entity_id=case.id,
    )

    await log_action(
        db=db, actor_id=officer.id, actor_email=officer.email,
        action="APPROVE_COMPENSATION", entity_type="compensation_case",
        entity_id=case.id, new_value={"status": "APPROVED"},
    )
    return case


async def process_payment(
    db: AsyncSession,
    case_id: UUID,
    amount: Decimal,
    method: str,
    reference: Optional[str],
    payment_date: datetime,
    officer: Profile,
) -> CompensationPayment:
    case = await get_compensation_case(db, case_id)
    if case.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compensation must be approved before payment",
        )

    payment = CompensationPayment(
        case_id=case_id,
        amount=amount,
        payment_method=method,
        payment_reference=reference,
        payment_date=payment_date,
        status="PENDING",
        approved_by=officer.id,
    )
    db.add(payment)
    await db.flush()

    case.status = "PAID"
    case.updated_at = datetime.utcnow()
    await db.flush()

    await log_action(
        db=db, actor_id=officer.id, actor_email=officer.email,
        action="PROCESS_PAYMENT", entity_type="compensation_payment",
        entity_id=payment.id,
        new_value={"amount": str(amount), "method": method},
    )
    return payment


async def get_compensation_summary(db: AsyncSession) -> dict:
    total_cases = (await db.execute(select(func.count(CompensationCase.id)))).scalar() or 0
    total_assessed = (await db.execute(
        select(func.coalesce(func.sum(CompensationCase.total_amount), 0))
    )).scalar() or Decimal("0")
    approved_count = (await db.execute(
        select(func.count(CompensationCase.id)).where(CompensationCase.status == "APPROVED")
    )).scalar() or 0
    paid_count = (await db.execute(
        select(func.count(CompensationCase.id)).where(CompensationCase.status == "PAID")
    )).scalar() or 0
    pending_count = total_cases - approved_count - paid_count
    return {
        "total_cases": total_cases,
        "total_assessed": float(total_assessed),
        "pending_count": pending_count,
        "approved_count": approved_count,
        "paid_count": paid_count,
    }
