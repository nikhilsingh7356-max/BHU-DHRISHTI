from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class JurisdictionRuleResponse(BaseModel):
    id: str
    rule_code: str
    rule_version: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    conditions: Any
    result: Any
    source_reference: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class JurisdictionDecisionResponse(BaseModel):
    id: str
    project_id: str
    rule_id: str
    suggested_appropriate_govt: Optional[str] = None
    suggested_acquiring_body: Optional[str] = None
    suggested_authority: Optional[str] = None
    confidence_score: Optional[float] = None
    reason: Optional[str] = None
    officer_verified: bool
    officer_id: Optional[str] = None
    officer_comment: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JurisdictionConfirm(BaseModel):
    confirmed: bool
    comment: Optional[str] = None
    override_appropriate_govt: Optional[str] = None
    override_acquiring_body: Optional[str] = None


class JurisdictionSuggestResponse(BaseModel):
    success: bool = True
    data: dict
