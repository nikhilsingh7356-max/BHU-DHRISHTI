from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class CompensationCreate(BaseModel):
    parcel_id: UUID
    project_id: UUID
    landowner_id: UUID
    assessed_value: Optional[Decimal] = None
    land_area_sq_m: Optional[Decimal] = None
    compensation_components: Optional[Any] = None
    total_amount: Optional[Decimal] = None
    assigned_officer_id: Optional[UUID] = None


class CompensationUpdate(BaseModel):
    assessed_value: Optional[Decimal] = None
    land_area_sq_m: Optional[Decimal] = None
    compensation_components: Optional[Any] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    assigned_officer_id: Optional[UUID] = None


class CompensationResponse(BaseModel):
    id: str
    parcel_id: str
    project_id: str
    landowner_id: str
    assessed_value: Optional[Decimal] = None
    land_area_sq_m: Optional[Decimal] = None
    compensation_components: Optional[Any] = None
    total_amount: Optional[Decimal] = None
    status: str
    assigned_officer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str
    payment_reference: Optional[str] = None
    payment_date: datetime


class PaymentResponse(BaseModel):
    id: str
    case_id: str
    amount: Decimal
    payment_method: str
    payment_reference: Optional[str] = None
    payment_date: datetime
    status: str
    approved_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompensationListResponse(BaseModel):
    success: bool = True
    data: List[CompensationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class CompensationSummary(BaseModel):
    total_cases: int = 0
    total_assessed: Decimal = Decimal("0")
    total_approved: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    pending_count: int = 0
    approved_count: int = 0
    paid_count: int = 0
