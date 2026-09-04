from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    previous_value: Optional[Any] = None
    new_value: Optional[Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    success: bool = True
    data: List[AuditLogResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class AuditFilters(BaseModel):
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
