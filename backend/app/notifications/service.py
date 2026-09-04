from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Notification, Profile, Role


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


async def notify_role(
    db: AsyncSession,
    role_id: UUID,
    title: str,
    message: str,
    notification_type: str = "INFO",
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
) -> None:
    result = await db.execute(
        select(Profile.id).where(Profile.role_id == role_id, Profile.is_active == True)  # noqa: E712
    )
    user_ids = [row[0] for row in result.all()]
    for uid in user_ids:
        await create_notification(
            db=db,
            user_id=uid,
            title=title,
            message=message,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )
