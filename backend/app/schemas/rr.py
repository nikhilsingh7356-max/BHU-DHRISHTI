from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class RRCaseCreate(BaseModel):
    project_id: UUID
    parcel_id: UUID
    landowner_id: UUID
    family_members_count: Optional[int] = Field(None, ge=0)
    eligibility_status: Optional[str] = "PENDING_REVIEW"
    entitlement_details: Optional[Any] = None
    assistance_type: Optional[str] = None
    assigned_officer_id: Optional[UUID] = None


class RRCaseUpdate(BaseModel):
    family_members_count: Optional[int] = Field(None, ge=0)
    eligibility_status: Optional[str] = None
    entitlement_details: Optional[Any] = None
    assistance_type: Optional[str] = None
    assigned_officer_id: Optional[UUID] = None
    status: Optional[str] = None


class RRCaseResponse(BaseModel):
    id: str
    project_id: str
    parcel_id: str
    landowner_id: str
    family_members_count: Optional[int] = None
    eligibility_status: str
    entitlement_details: Optional[Any] = None
    assistance_type: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RRCaseListResponse(BaseModel):
    success: bool = True
    data: List[RRCaseResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class ObjectionCreate(BaseModel):
    project_id: UUID
    parcel_id: Optional[UUID] = None
    landowner_id: Optional[UUID] = None
    category: str = Field(..., max_length=50)
    description: str = Field(..., min_length=10)


class ObjectionResponse(BaseModel):
    id: str
    objection_code: str
    project_id: str
    parcel_id: Optional[str] = None
    landowner_id: Optional[str] = None
    submission_date: Optional[datetime] = None
    category: str
    description: str
    status: str
    created_by: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ObjectionListResponse(BaseModel):
    success: bool = True
    data: List[ObjectionResponse] = []
    total: int = 0


class HearingCreate(BaseModel):
    objection_id: UUID
    hearing_date: datetime
    location: Optional[str] = None


class HearingResponse(BaseModel):
    id: str
    objection_id: str
    hearing_date: datetime
    hearing_officer_id: str
    location: Optional[str] = None
    decision: Optional[str] = None
    decision_details: Optional[str] = None
    decision_date: Optional[datetime] = None
    next_hearing_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HearingListResponse(BaseModel):
    success: bool = True
    data: List[HearingResponse] = []
    total: int = 0
