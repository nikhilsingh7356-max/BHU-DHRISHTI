from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    success: bool = True
    data: List[NotificationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    unread_count: int = 0
