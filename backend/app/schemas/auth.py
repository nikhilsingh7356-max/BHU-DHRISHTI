from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = None
    role_id: UUID
    department_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PermissionResponse(BaseModel):
    id: str
    name: str
    module: str

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: Optional[RoleResponse] = None
    department_id: Optional[str] = None
    state_id: Optional[str] = None
    district_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithPermissions(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: Optional[RoleResponse] = None
    permissions: List[PermissionResponse] = []
    department_id: Optional[str] = None
    state_id: Optional[str] = None
    district_id: Optional[str] = None
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = None
    role_id: UUID
    department_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    is_active: bool = True


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=20)
    parent_id: Optional[UUID] = None
    level: int = 1
    state_code: Optional[str] = None
    district_code: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: str
    parent_id: Optional[str] = None
    level: int
    state_code: Optional[str] = None
    district_code: Optional[str] = None

    class Config:
        from_attributes = True


class SLARuleCreate(BaseModel):
    from_status: str
    to_status: str
    max_duration_hours: int = Field(..., gt=0)
    role_id: Optional[UUID] = None
    priority: int = Field(default=3, ge=1, le=5)
    is_active: bool = True


class SLARuleResponse(BaseModel):
    id: str
    from_status: str
    to_status: str
    max_duration_hours: int
    role_id: Optional[str] = None
    priority: int
    is_active: bool

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    success: bool = True
    data: List = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: str = "Operation successful"


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
