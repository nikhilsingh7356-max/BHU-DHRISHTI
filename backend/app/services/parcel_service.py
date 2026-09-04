from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.models import Parcel, ParcelOwner, Village, Tehsil, District, State
from app.audit.service import log_action
from app.gis.spatial_ops import calculate_area_from_geojson


async def generate_parcel_code(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(Parcel.id)))
    count = result.scalar() or 0
    return f"PRC-{count + 1:06d}"


async def create_parcel(
    db: AsyncSession,
    data,
    user,
    ip: str = None,
    user_agent: str = None,
) -> Parcel:
    parcel_code = await generate_parcel_code(db)

    if data.ulpin:
        result = await db.execute(select(Parcel).where(Parcel.ulpin == data.ulpin))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Parcel with this ULPIN already exists")

    area = data.area_sq_m
    geom_area = calculate_area_from_geojson(data.geometry) if data.geometry else None
    if geom_area and area and abs(float(geom_area) - float(area)) / float(area) > 0.05:
        pass  # Log but don't block on creation

    parcel = Parcel(
        parcel_code=parcel_code,
        survey_number=data.survey_number,
        khasra_number=data.khasra_number,
        ulpin=data.ulpin,
        village_id=data.village_id,
        tehsil_id=data.tehsil_id,
        district_id=data.district_id,
        state_id=data.state_id,
        land_type=data.land_type,
        ownership_type=data.ownership_type,
        area_sq_m=area,
        geometry=data.geometry,
        current_status="IDENTIFIED",
    )
    db.add(parcel)
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="CREATE_PARCEL", entity_type="parcel", entity_id=parcel.id,
        new_value={"parcel_code": parcel_code, "khasra": data.khasra_number, "area": str(area)},
        ip_address=ip, user_agent=user_agent,
    )
    return parcel


async def list_parcels(
    db: AsyncSession,
    state_id=None, district_id=None, tehsil_id=None, village_id=None,
    land_type=None, ownership_type=None, current_status=None,
    search=None, page=1, page_size=20,
):
    query = select(Parcel).options(selectinload(Parcel.owners))
    count_query = select(func.count(Parcel.id))

    conditions = []
    if state_id:
        conditions.append(Parcel.state_id == state_id)
    if district_id:
        conditions.append(Parcel.district_id == district_id)
    if tehsil_id:
        conditions.append(Parcel.tehsil_id == tehsil_id)
    if village_id:
        conditions.append(Parcel.village_id == village_id)
    if land_type:
        conditions.append(Parcel.land_type == land_type)
    if ownership_type:
        conditions.append(Parcel.ownership_type == ownership_type)
    if current_status:
        conditions.append(Parcel.current_status == current_status)
    if search:
        like = f"%{search}%"
        conditions.append(or_(
            Parcel.survey_number.ilike(like),
            Parcel.khasra_number.ilike(like),
            Parcel.parcel_code.ilike(like),
            Parcel.ulpin.ilike(like),
        ))

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(desc(Parcel.created_at))
        .offset((page - 1) * page_size).limit(page_size)
    )
    parcels = result.scalars().unique().all()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "data": parcels, "total": total, "page": page,
        "page_size": page_size, "total_pages": total_pages,
    }


async def get_parcel(db: AsyncSession, parcel_id: UUID) -> Parcel:
    result = await db.execute(
        select(Parcel)
        .options(
            selectinload(Parcel.owners),
            selectinload(Parcel.village),
            selectinload(Parcel.tehsil),
            selectinload(Parcel.district),
            selectinload(Parcel.state),
        )
        .where(Parcel.id == parcel_id)
    )
    parcel = result.scalar_one_or_none()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


async def update_parcel(
    db: AsyncSession, parcel_id: UUID, data, user,
    ip=None, user_agent=None,
) -> Parcel:
    parcel = await get_parcel(db, parcel_id)

    update_fields = {}
    if data.survey_number is not None:
        parcel.survey_number = data.survey_number
        update_fields["survey_number"] = data.survey_number
    if data.khasra_number is not None:
        parcel.khasra_number = data.khasra_number
        update_fields["khasra_number"] = data.khasra_number
    if data.ulpin is not None:
        parcel.ulpin = data.ulpin
        update_fields["ulpin"] = data.ulpin
    if data.land_type is not None:
        parcel.land_type = data.land_type
        update_fields["land_type"] = data.land_type
    if data.ownership_type is not None:
        parcel.ownership_type = data.ownership_type
        update_fields["ownership_type"] = data.ownership_type
    if data.area_sq_m is not None:
        parcel.area_sq_m = data.area_sq_m
        update_fields["area_sq_m"] = str(data.area_sq_m)
    if data.geometry is not None:
        parcel.geometry = data.geometry
        update_fields["geometry"] = data.geometry
    if data.current_status is not None:
        parcel.current_status = data.current_status
        update_fields["current_status"] = data.current_status

    parcel.updated_at = datetime.utcnow()
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="UPDATE_PARCEL", entity_type="parcel", entity_id=parcel.id,
        new_value=update_fields, ip_address=ip, user_agent=user_agent,
    )
    return parcel


async def add_owner(db: AsyncSession, parcel_id: UUID, data, user) -> ParcelOwner:
    parcel = await get_parcel(db, parcel_id)
    if data.is_primary:
        result = await db.execute(
            select(ParcelOwner).where(
                ParcelOwner.parcel_id == parcel_id,
                ParcelOwner.is_primary == True  # noqa: E712
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.is_primary = False

    owner = ParcelOwner(
        parcel_id=parcel_id,
        owner_name=data.owner_name,
        father_husband_name=data.father_husband_name,
        gender=data.gender,
        age=data.age,
        aadhaar_last4=data.aadhaar_last4,
        relation_to_holder=data.relation_to_holder,
        is_primary=data.is_primary,
        contact_phone=data.contact_phone,
        address=data.address,
    )
    db.add(owner)
    await db.flush()
    return owner


async def get_parcels_for_project(db: AsyncSession, project_id: UUID) -> list:
    result = await db.execute(
        select(Parcel)
        .join(ProjectParcel, ProjectParcel.parcel_id == Parcel.id)
        .where(ProjectParcel.project_id == project_id)
        .options(selectinload(Parcel.owners))
    )
    return result.scalars().all()
