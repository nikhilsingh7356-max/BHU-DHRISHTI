from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status
from app.models.models import (
    WorkflowInstance, WorkflowTask, WorkflowTransition, Project,
    ProjectStatusHistory, SLARule, SLAEvent, Notification, ProjectActivity,
    Profile, Role
)
from app.workflow.engine import (
    validate_transition,
    get_allowed_transitions,
    get_task_type_for_transition,
    get_task_role_for_transition,
)
from app.audit.service import log_action
from app.notifications.service import create_notification, notify_role


VALID_TRANSITIONS = {
    "DRAFT": ["SUBMITTED", "CANCELLED"],
    "SUBMITTED": ["UNDER_REVIEW", "REJECTED", "DRAFT"],
    "UNDER_REVIEW": ["JURISDICTION_CHECK", "GIS_VERIFICATION", "REJECTED", "SUBMITTED"],
    "JURISDICTION_CHECK": ["GIS_VERIFICATION", "PUBLIC_HEARING", "REJECTED"],
    "GIS_VERIFICATION": ["PUBLIC_HEARING", "JURISDICTION_CHECK", "REJECTED"],
    "PUBLIC_HEARING": ["COMPENSATION_ASSESSMENT", "RR_PLANNING", "REJECTED", "GIS_VERIFICATION"],
    "COMPENSATION_ASSESSMENT": ["APPROVED", "REJECTED", "RR_PLANNING", "PUBLIC_HEARING"],
    "RR_PLANNING": ["APPROVED", "REJECTED", "COMPENSATION_ASSESSMENT", "PUBLIC_HEARING"],
    "APPROVED": ["IN_PROGRESS", "COMPLETED", "RR_PLANNING", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED", "CANCELLED", "REJECTED"],
    "COMPLETED": [],
    "REJECTED": ["DRAFT", "UNDER_REVIEW", "CANCELLED"],
    "CANCELLED": [],
}


class WorkflowException(HTTPException):
    pass


async def transition_status(
    db: AsyncSession,
    project_id: UUID,
    new_status: str,
    actor: Profile,
    comment: Optional[str] = None,
    supporting_document_id: Optional[UUID] = None,
    ip: str = None,
    user_agent: str = None,
):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    previous_status = project.status

    if previous_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project is already in status {new_status}",
        )

    if not validate_transition(previous_status, new_status):
        allowed = get_allowed_transitions(previous_status)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {previous_status} to {new_status}. Allowed: {allowed}",
        )

    project.status = new_status
    project.updated_at = datetime.utcnow()

    result = await db.execute(
        select(WorkflowInstance).where(WorkflowInstance.project_id == project_id)
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        instance = WorkflowInstance(project_id=project_id, current_status=new_status)
        db.add(instance)
        await db.flush()
    else:
        instance.current_status = new_status
        instance.updated_at = datetime.utcnow()

    history = ProjectStatusHistory(
        project_id=project_id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=actor.id,
        comment=comment,
    )
    db.add(history)

    task_type = get_task_type_for_transition(new_status)
    role_name = get_task_role_for_transition(new_status)

    result = await db.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    role_id = role.id if role else None

    workflow_task = WorkflowTask(
        instance_id=instance.id,
        assigned_role_id=role_id,
        task_type=task_type,
        title=f"Process transition to {new_status}",
        description=comment,
        status="PENDING",
        started_at=datetime.utcnow(),
    )
    db.add(workflow_task)
    await db.flush()

    transition = WorkflowTransition(
        instance_id=instance.id,
        task_id=workflow_task.id,
        from_status=previous_status,
        to_status=new_status,
        actor_id=actor.id,
        actor_role=actor.role.name if actor.role else None,
        comment=comment,
        supporting_document_id=supporting_document_id,
    )
    db.add(transition)

    sla_result = await db.execute(
        select(SLARule).where(
            SLARule.from_status == previous_status,
            SLARule.to_status == new_status,
            SLARule.is_active == True  # noqa: E712
        )
    )
    sla_rule = sla_result.scalar_one_or_none()
    if sla_rule:
        deadline = datetime.utcnow() + timedelta(hours=sla_rule.max_duration_hours)
        sla_event = SLAEvent(
            workflow_task_id=workflow_task.id,
            rule_id=sla_rule.id,
            status="ON_TRACK",
            deadline=deadline,
        )
        db.add(sla_event)
        workflow_task.sla_deadline = deadline

    activity = ProjectActivity(
        project_id=project_id,
        actor_id=actor.id,
        activity_type="STATUS_CHANGE",
        description=f"Status changed from {previous_status} to {new_status}",
        meta={"from": previous_status, "to": new_status, "comment": comment},
    )
    db.add(activity)

    await create_notification(
        db=db,
        user_id=project.created_by,
        title="Project Status Update",
        message=f"Project {project.project_code} status changed from {previous_status} to {new_status}",
        notification_type="STATUS_CHANGE",
        entity_type="project",
        entity_id=project.id,
    )

    await db.flush()

    await log_action(
        db=db,
        actor_id=actor.id,
        actor_email=actor.email,
        action="WORKFLOW_TRANSITION",
        entity_type="project",
        entity_id=project.id,
        previous_value={"status": previous_status},
        new_value={"status": new_status, "task_id": str(workflow_task.id)},
        ip_address=ip,
        user_agent=user_agent,
    )

    return {
        "transition": transition,
        "task": workflow_task,
        "instance": instance,
        "project": project,
    }


async def get_workflow_state(db: AsyncSession, project_id: UUID) -> dict:
    result = await db.execute(
        select(WorkflowInstance)
        .options(
            __import__("sqlalchemy").orm.selectinload(WorkflowInstance.tasks),
            __import__("sqlalchemy").orm.selectinload(WorkflowInstance.transitions),
        )
        .where(WorkflowInstance.project_id == project_id)
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise HTTPException(status_code=404, detail="Workflow instance not found")

    allowed = get_allowed_transitions(instance.current_status)

    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    return {
        "instance": instance,
        "current_status": instance.current_status,
        "allowed_transitions": allowed,
        "project": project,
    }


async def get_workflow_tasks(db: AsyncSession, project_id: UUID) -> list:
    result = await db.execute(
        select(WorkflowInstance).where(WorkflowInstance.project_id == project_id)
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    result = await db.execute(
        select(WorkflowTask)
        .where(WorkflowTask.instance_id == instance.id)
        .order_by(WorkflowTask.created_at)
    )
    return result.scalars().all()


async def check_sla_status(db: AsyncSession, task_id: UUID) -> str:
    result = await db.execute(select(WorkflowTask).where(WorkflowTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in ("COMPLETED", "CANCELLED"):
        return task.status

    if task.sla_deadline and datetime.utcnow() > task.sla_deadline:
        task.status = "OVERDUE"
        result = await db.execute(
            select(SLAEvent).where(SLAEvent.workflow_task_id == task.id)
        )
        sla_event = result.scalar_one_or_none()
        if sla_event:
            sla_event.status = "BREACHED"
            sla_event.escalation_level += 1
        await db.flush()
        return "OVERDUE"

    return "ON_TRACK"
