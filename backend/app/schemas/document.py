from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DocumentCreate(BaseModel):
    project_id: UUID
    parcel_id: Optional[UUID] = None
    document_type: str
    title: str = Field(..., min_length=1, max_length=300)
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    parcel_id: Optional[str] = None
    document_type: str
    title: str
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    status: str
    uploaded_by: str
    verified_by: Optional[str] = None
    verification_comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentVerify(BaseModel):
    status: str = Field(..., pattern=r"^(APPROVED|REJECTED)$")
    comment: Optional[str] = None


class DocumentListResponse(BaseModel):
    success: bool = True
    data: List[DocumentResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
