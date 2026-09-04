from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services.search_service import (
    list_notifications, mark_notification_read, mark_all_notifications_read
)
from app.models.models import Profile

router = APIRouter()


@router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await list_notifications(
        db, current_user.id, page, page_size, unread_only
    )
    data = []
    for n in result["data"]:
        data.append({
            "id": str(n.id),
            "user_id": str(n.user_id),
            "title": n.title,
            "message": n.message,
            "notification_type": n.notification_type,
            "entity_type": n.entity_type,
            "entity_id": str(n.entity_id) if n.entity_id else None,
            "is_read": n.is_read,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "unread_count": result["unread_count"],
        "message": "Notifications retrieved",
    }


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    try:
        notification = await mark_notification_read(db, notification_id, current_user.id)
    except Exception:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {
        "success": True,
        "data": {"id": str(notification.id), "is_read": True},
        "message": "Notification marked as read",
    }


@router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    count = await mark_all_notifications_read(db, current_user.id)
    return {
        "success": True,
        "data": {"marked_read": count},
        "message": f"{count} notifications marked as read",
    }
