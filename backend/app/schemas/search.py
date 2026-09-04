from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID


class SearchResultItem(BaseModel):
    entity_type: str
    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Any] = None


class SearchResponse(BaseModel):
    success: bool = True
    data: List[SearchResultItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class SearchFilters(BaseModel):
    query: str
    entity_types: Optional[List[str]] = None
    status: Optional[str] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    page: int = 1
    page_size: int = 20


class DashboardStats(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    total_parcels: int = 0
    total_area_sq_m: float = 0
    total_documents: int = 0
    pending_compensation: int = 0
    total_compensation_amount: float = 0
    open_objections: int = 0
    sla_breaches: int = 0
    users_count: int = 0


class ReportSummary(BaseModel):
    success: bool = True
    data: dict
