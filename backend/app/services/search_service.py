from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.models import (
    Notification, Project, Parcel, ProjectDocument, AuditLog
)
from app.audit.service import log_action


async def create_objection(
    db: AsyncSession,
    data,
    user,
) -> object:
    from app.models.models import Objection
    count = (await db.execute(select(func.count(Objection.id)))).scalar() or 0
    objection_code = f"OBJ-{count + 1:05d}"

    objection = Objection(
        objection_code=objection_code,
        project_id=data.project_id,
        parcel_id=data.parcel_id,
        landowner_id=data.landowner_id,
        category=data.category,
        description=data.description,
        status="SUBMITTED",
        created_by=user.id,
    )
    db.add(objection)
    await db.flush()

    await log_action(
        db=db, actor_id=user.id, actor_email=user.email,
        action="CREATE_OBJECTION", entity_type="objection",
        entity_id=objection.id,
        new_value={"objection_code": objection_code, "category": data.category},
    )
    return objection


async def list_objections(
    db: AsyncSession,
    project_id: UUID = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    from app.models.models import Objection
    query = select(Objection)
    count_query = select(func.count(Objection.id))
    if project_id:
        query = query.where(Objection.project_id == project_id)
        count_query = count_query.where(Objection.project_id == project_id)
    if status_filter:
        query = query.where(Objection.status == status_filter)
        count_query = count_query.where(Objection.status == status_filter)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Objection.submission_date.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    return {
        "data": items, "total": total, "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }


async def schedule_hearing(
    db: AsyncSession,
    objection_id: UUID,
    hearing_date: datetime,
    officer_id: UUID,
    location: Optional[str],
) -> object:
    from app.models.models import Objection, Hearing
    result = await db.execute(select(Objection).where(Objection.id == objection_id))
    objection = result.scalar_one_or_none()
    if objection is None:
        raise Exception("Objection not found")

    hearing = Hearing(
        objection_id=objection_id,
        hearing_date=hearing_date,
        hearing_officer_id=officer_id,
        location=location,
    )
    db.add(hearing)
    objection.status = "HEARING_SCHEDULED"
    await db.flush()
    return hearing


async def list_hearings(db: AsyncSession, objection_id: UUID = None) -> list:
    from app.models.models import Hearing
    query = select(Hearing)
    if objection_id:
        query = query.where(Hearing.objection_id == objection_id)
    result = await db.execute(query.order_by(Hearing.hearing_date))
    return result.scalars().all()


async def get_unread_notifications_count(db: AsyncSession, user_id: UUID) -> int:
    count = (await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False  # noqa: E712
        )
    )).scalar() or 0
    return count


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> dict:
    query = select(Notification).where(Notification.user_id == user_id)
    count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
        count_query = count_query.where(Notification.is_read == False)  # noqa: E712
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    unread_count = await get_unread_notifications_count(db, user_id)
    return {
        "data": items, "total": total, "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        "unread_count": unread_count,
    }


async def mark_notification_read(db: AsyncSession, notification_id: UUID, user_id: UUID):
    from app.models.models import Notification
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise Exception("Notification not found")
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.flush()
    return notification


async def mark_all_notifications_read(db: AsyncSession, user_id: UUID) -> int:
    from app.models.models import Notification
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False  # noqa: E712
        )
    )
    notifications = result.scalars().all()
    for n in notifications:
        n.is_read = True
        n.read_at = datetime.utcnow()
    await db.flush()
    return len(notifications)


async def global_search(
    db: AsyncSession,
    query_text: str,
    entity_types=None,
    status_filter=None,
    state_id=None,
    district_id=None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    like = f"%{query_text}%"
    results = []

    project_query = select(Project).where(or_(
        Project.name.ilike(like),
        Project.project_code.ilike(like),
        Project.description.ilike(like),
    ))
    if status_filter:
        project_query = project_query.where(Project.status == status_filter)
    if state_id:
        project_query = project_query.where(Project.state_id == state_id)
    if district_id:
        project_query = project_query.where(Project.district_id == district_id)
    if not entity_types or "project" in entity_types:
        projects = (await db.execute(project_query.limit(page_size))).scalars().all()
        for p in projects:
            results.append({
                "entity_type": "project",
                "id": str(p.id),
                "title": p.name,
                "description": p.description,
                "status": p.status,
                "metadata": {"project_code": p.project_code},
            })

    if not entity_types or "parcel" in entity_types:
        parcel_query = select(Parcel).where(or_(
            Parcel.survey_number.ilike(like),
            Parcel.khasra_number.ilike(like),
            Parcel.parcel_code.ilike(like),
            Parcel.ulpin.ilike(like),
        ))
        parcels = (await db.execute(parcel_query.limit(page_size))).scalars().all()
        for p in parcels:
            results.append({
                "entity_type": "parcel",
                "id": str(p.id),
                "title": f"Parcel {p.parcel_code}",
                "description": f"Khasra: {p.khasra_number}, Survey: {p.survey_number}",
                "status": p.current_status,
                "metadata": {"area_sq_m": str(p.area_sq_m)},
            })

    if not entity_types or "document" in entity_types:
        doc_query = select(ProjectDocument).where(or_(
            ProjectDocument.title.ilike(like),
            ProjectDocument.file_name.ilike(like),
        ))
        docs = (await db.execute(doc_query.limit(page_size))).scalars().all()
        for d in docs:
            results.append({
                "entity_type": "document",
                "id": str(d.id),
                "title": d.title,
                "description": f"Type: {d.document_type}",
                "status": d.status,
                "metadata": {"file_name": d.file_name},
            })

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": results[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
