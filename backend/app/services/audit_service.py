from datetime import datetime
from uuid import UUID
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.models import AuditLog, Notification
from app.audit.service import log_action as _log_action


async def log_action(
    db: AsyncSession,
    actor_id: Optional[UUID],
    actor_email: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[UUID] = None,
    previous_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Any] = None,
) -> AuditLog:
    return await _log_action(
        db=db, actor_id=actor_id, actor_email=actor_email,
        action=action, entity_type=entity_type, entity_id=entity_id,
        previous_value=previous_value, new_value=new_value,
        ip_address=ip_address, user_agent=user_agent, metadata=metadata,
    )


async def get_audit_logs(
    db: AsyncSession,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if entity_type:
        conditions.append(AuditLog.entity_type == entity_type)
    if entity_id:
        conditions.append(AuditLog.entity_id == entity_id)
    if actor_id:
        conditions.append(AuditLog.actor_id == actor_id)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    logs = result.scalars().all()
    return {
        "data": logs, "total": total, "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }


async def create_notification(
    db: AsyncSession,
    user_id: Optional[UUID],
    title: str,
    message: str,
    notification_type: str = "INFO",
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(notification)
    await db.flush()
    return notification
