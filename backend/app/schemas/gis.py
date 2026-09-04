from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class GISVerifyRequest(BaseModel):
    officer_id: UUID


class GISVerificationResponse(BaseModel):
    id: str
    project_id: str
    parcel_id: str
    verified_by: Optional[str] = None
    geometry_valid: Optional[bool] = None
    area_match: Optional[bool] = None
    overlap_detected: Optional[bool] = None
    overlap_parcel_ids: Optional[List[str]] = None
    outside_boundary: Optional[bool] = None
    conflict_details: Optional[Any] = None
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GISOverlapCheckRequest(BaseModel):
    parcel_id: UUID
    geometry: Any


class GISOverlapCheckResponse(BaseModel):
    success: bool = True
    data: dict


class GISProjectVerificationsResponse(BaseModel):
    success: bool = True
    data: List[GISVerificationResponse] = []
    total: int = 0
