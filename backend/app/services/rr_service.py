from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from app.models.models import RRCase, Parcel, ParcelOwner, Project, Profile
from app.audit.service import log_action


async def create_rr_case(
    db: AsyncSession,
    data,
    user: Profile,
) -> RRCase:
    result = await db.execute(select(Project).where(Project.id == data.project_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await db.execute(select(Parcel).where(Parcel.id == data.parcel_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    result = await db.execute(select(ParcelOwner).where(ParcelOwner.id == data.landowner_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Landowner not found")

    case = RRCase(
        project_id=data.project_id,
        parcel_id=data.parcel_id,
        landowner_id=data.landowner_id,
        family_members_count=data.family_members_count,
        eligibility_status=data.eligibility_status,
        entitlement_details=data.entitlement_details,
        assistance_type=data.assistance_type,
        assigned_officer_id=data.assigned_officer_id,
        status=data.eligibility_status or "PENDING_REVIEW",
    )
    db.add(case)
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="CREATE_RR_CASE", entity_type="rr_case", entity_id=case.id,
        new_value={"parcel_id": str(data.parcel_id), "status": case.status},
    )
    return case


async def list_rr_cases(
    db: AsyncSession,
    project_id: UUID = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(RRCase)
    count_query = select(func.count(RRCase.id))
    if project_id:
        query = query.where(RRCase.project_id == project_id)
        count_query = count_query.where(RRCase.project_id == project_id)
    if status_filter:
        query = query.where(RRCase.status == status_filter)
        count_query = count_query.where(RRCase.status == status_filter)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(RRCase.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    cases = result.scalars().all()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "data": cases, "total": total, "page": page,
        "page_size": page_size, "total_pages": total_pages,
    }


async def get_rr_case(db: AsyncSession, case_id: UUID) -> RRCase:
    result = await db.execute(select(RRCase).where(RRCase.id == case_id))
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail="RR case not found")
    return case


async def update_rr_case(db: AsyncSession, case_id: UUID, data, user: Profile) -> RRCase:
    case = await get_rr_case(db, case_id)
    if data.family_members_count is not None:
        case.family_members_count = data.family_members_count
    if data.eligibility_status is not None:
        case.eligibility_status = data.eligibility_status
        case.status = data.eligibility_status
    if data.entitlement_details is not None:
        case.entitlement_details = data.entitlement_details
    if data.assistance_type is not None:
        case.assistance_type = data.assistance_type
    if data.assigned_officer_id is not None:
        case.assigned_officer_id = data.assigned_officer_id
    if data.status is not None:
        case.status = data.status
    case.updated_at = datetime.utcnow()
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="UPDATE_RR_CASE", entity_type="rr_case", entity_id=case.id,
        new_value={"status": case.status},
    )
    return case
