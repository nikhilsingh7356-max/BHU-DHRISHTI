from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ParcelCreate(BaseModel):
    survey_number: Optional[str] = None
    khasra_number: Optional[str] = None
    ulpin: Optional[str] = None
    village_id: UUID
    tehsil_id: UUID
    district_id: UUID
    state_id: UUID
    land_type: str = "AGRICULTURAL"
    ownership_type: str = "PRIVATE"
    area_sq_m: Decimal = Field(..., gt=0)
    geometry: Optional[Any] = None


class ParcelUpdate(BaseModel):
    survey_number: Optional[str] = None
    khasra_number: Optional[str] = None
    ulpin: Optional[str] = None
    land_type: Optional[str] = None
    ownership_type: Optional[str] = None
    area_sq_m: Optional[Decimal] = Field(None, gt=0)
    geometry: Optional[Any] = None
    current_status: Optional[str] = None


class ParcelOwnerCreate(BaseModel):
    owner_name: str = Field(..., min_length=2, max_length=200)
    father_husband_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    aadhaar_last4: Optional[str] = Field(None, max_length=4)
    relation_to_holder: Optional[str] = None
    is_primary: bool = True
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class ParcelOwnerResponse(BaseModel):
    id: str
    parcel_id: str
    owner_name: str
    father_husband_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    aadhaar_last4: Optional[str] = None
    relation_to_holder: Optional[str] = None
    is_primary: bool
    contact_phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True


class ParcelResponse(BaseModel):
    id: str
    parcel_code: str
    survey_number: Optional[str] = None
    khasra_number: Optional[str] = None
    ulpin: Optional[str] = None
    village_id: str
    tehsil_id: str
    district_id: str
    state_id: str
    land_type: str
    ownership_type: str
    area_sq_m: Decimal
    geometry: Optional[Any] = None
    current_status: str
    created_at: Optional[datetime] = None
    owners: List[ParcelOwnerResponse] = []

    class Config:
        from_attributes = True


class ParcelListResponse(BaseModel):
    success: bool = True
    data: List[ParcelResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class ParcelFilters(BaseModel):
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    tehsil_id: Optional[UUID] = None
    village_id: Optional[UUID] = None
    land_type: Optional[str] = None
    ownership_type: Optional[str] = None
    current_status: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20
