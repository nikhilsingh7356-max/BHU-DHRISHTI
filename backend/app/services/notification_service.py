from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Notification
from app.notifications.service import create_notification, notify_role


async def create_notification_wrapper(
    db: AsyncSession,
    user_id: Optional[UUID],
    title: str,
    message: str,
    notification_type: str = "INFO",
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
) -> Notification:
    return await create_notification(
        db=db, user_id=user_id, title=title, message=message,
        notification_type=notification_type,
        entity_type=entity_type, entity_id=entity_id,
    )


async def notify_role_wrapper(
    db: AsyncSession,
    role_id: UUID,
    title: str,
    message: str,
    notification_type: str = "INFO",
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
):
    await notify_role(
        db=db, role_id=role_id, title=title, message=message,
        notification_type=notification_type,
        entity_type=entity_type, entity_id=entity_id,
    )
