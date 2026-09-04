from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class WorkflowTransitionRequest(BaseModel):
    new_status: str
    comment: Optional[str] = None
    supporting_document_id: Optional[UUID] = None


class WorkflowTaskResponse(BaseModel):
    id: str
    instance_id: str
    assigned_to: Optional[str] = None
    assigned_role_id: Optional[str] = None
    task_type: str
    title: str
    description: Optional[str] = None
    status: str
    sla_deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowTransitionResponse(BaseModel):
    id: str
    instance_id: str
    from_status: str
    to_status: str
    actor_id: str
    actor_role: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowInstanceResponse(BaseModel):
    id: str
    project_id: str
    current_status: str
    tasks: List[WorkflowTaskResponse] = []
    transitions: List[WorkflowTransitionResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowHistoryResponse(BaseModel):
    success: bool = True
    data: dict
