from uuid import UUID
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog


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
    log = AuditLog(
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_value=previous_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
        meta=metadata,
    )
    db.add(log)
    await db.flush()
    return log
