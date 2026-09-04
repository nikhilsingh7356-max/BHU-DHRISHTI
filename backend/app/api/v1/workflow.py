from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import workflow_service
from app.models.models import Profile
from app.schemas.workflow import WorkflowTransitionRequest

router = APIRouter()


@router.get("/project/{project_id}")
async def get_workflow_state(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await workflow_service.get_workflow_state(db, project_id)
    instance = result["instance"]

    tasks = []
    for t in (instance.tasks or []):
        tasks.append({
            "id": str(t.id),
            "instance_id": str(t.instance_id),
            "assigned_to": str(t.assigned_to) if t.assigned_to else None,
            "assigned_role_id": str(t.assigned_role_id) if t.assigned_role_id else None,
            "task_type": t.task_type,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        })

    transitions = []
    for tr in (instance.transitions or []):
        transitions.append({
            "id": str(tr.id),
            "instance_id": str(tr.instance_id),
            "from_status": tr.from_status,
            "to_status": tr.to_status,
            "actor_id": str(tr.actor_id),
            "actor_role": tr.actor_role,
            "comment": tr.comment,
            "created_at": tr.created_at.isoformat() if tr.created_at else None,
        })

    return {
        "success": True,
        "data": {
            "instance_id": str(instance.id),
            "project_id": str(project_id),
            "current_status": instance.current_status,
            "allowed_transitions": result["allowed_transitions"],
            "tasks": tasks,
            "transitions": transitions,
        },
        "message": "Workflow state retrieved",
    }


@router.post("/project/{project_id}/transition")
async def execute_transition(
    project_id: UUID,
    data: WorkflowTransitionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    try:
        result = await workflow_service.transition_status(
            db=db,
            project_id=project_id,
            new_status=data.new_status,
            actor=current_user,
            comment=data.comment,
            supporting_document_id=data.supporting_document_id,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except HTTPException:
        raise

    return {
        "success": True,
        "data": {
            "from_status": result["transition"].from_status,
            "to_status": result["transition"].to_status,
            "task_id": str(result["task"].id),
            "task_status": result["task"].status,
            "project_status": result["project"].status,
        },
        "message": f"Status changed from {result['transition'].from_status} to {result['transition'].to_status}",
    }


@router.get("/project/{project_id}/tasks")
async def list_tasks(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    tasks = await workflow_service.get_workflow_tasks(db, project_id)
    return {
        "success": True,
        "data": [
            {
                "id": str(t.id),
                "instance_id": str(t.instance_id),
                "assigned_to": str(t.assigned_to) if t.assigned_to else None,
                "assigned_role_id": str(t.assigned_role_id) if t.assigned_role_id else None,
                "task_type": t.task_type,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ],
        "message": "Workflow tasks retrieved",
    }
