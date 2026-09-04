from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    project_type: str = Field(..., max_length=50)
    purpose: Optional[str] = None
    public_category: Optional[str] = None
    sponsor_id: Optional[UUID] = None
    land_requiring_body_id: Optional[UUID] = None
    proposed_area_sq_m: Optional[Decimal] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    tehsil_id: Optional[UUID] = None
    village_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    priority: int = Field(default=3, ge=1, le=5)
    estimated_cost: Optional[Decimal] = None
    funding_source: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = None
    project_type: Optional[str] = None
    purpose: Optional[str] = None
    public_category: Optional[str] = None
    sponsor_id: Optional[UUID] = None
    land_requiring_body_id: Optional[UUID] = None
    proposed_area_sq_m: Optional[Decimal] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    tehsil_id: Optional[UUID] = None
    village_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    estimated_cost: Optional[Decimal] = None
    funding_source: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    project_code: str
    name: str
    description: Optional[str] = None
    project_type: str
    purpose: Optional[str] = None
    public_category: Optional[str] = None
    sponsor_id: Optional[str] = None
    land_requiring_body_id: Optional[str] = None
    proposed_area_sq_m: Optional[Decimal] = None
    state_id: Optional[str] = None
    district_id: Optional[str] = None
    tehsil_id: Optional[str] = None
    village_id: Optional[str] = None
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    priority: int
    estimated_cost: Optional[Decimal] = None
    funding_source: Optional[str] = None
    status: str
    created_by: str
    version: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    success: bool = True
    data: List[ProjectResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class ProjectTimelineEntry(BaseModel):
    id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_by: str
    comment: Optional[str] = None
    changed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectActivityEntry(BaseModel):
    id: str
    actor_id: str
    activity_type: str
    description: str
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectSubmit(BaseModel):
    comment: Optional[str] = None
    supporting_document_id: Optional[UUID] = None


class ProjectFilters(BaseModel):
    status: Optional[str] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    project_type: Optional[str] = None
    search: Optional[str] = None
    priority: Optional[int] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
