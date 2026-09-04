from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import SLAEvent, WorkflowTask, SLARule, WorkflowInstance


async def check_sla_status(db: AsyncSession, task_id: UUID) -> str:
    result = await db.execute(select(WorkflowTask).where(WorkflowTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        return "NOT_FOUND"

    if task.status == "COMPLETED":
        return "COMPLETED"
    if task.status == "CANCELLED":
        return "CANCELLED"

    if task.sla_deadline and datetime.utcnow() > task.sla_deadline:
        task.status = "OVERDUE"
        result = await db.execute(
            select(SLAEvent).where(SLAEvent.workflow_task_id == task.id).order_by(SLAEvent.created_at.desc())
        )
        sla_event = result.scalar_one_or_none()
        if sla_event:
            sla_event.status = "BREACHED"
            sla_event.escalation_level += 1
        await db.flush()
        return "OVERDUE"

    return "ON_TRACK"


async def get_sla_dashboard(
    db: AsyncSession,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> dict:
    total_tasks = (await db.execute(select(func.count(WorkflowTask.id)))).scalar() or 0
    overdue_tasks = (await db.execute(
        select(func.count(WorkflowTask.id)).where(
            WorkflowTask.status == "OVERDUE"
        )
    )).scalar() or 0
    completed_tasks = (await db.execute(
        select(func.count(WorkflowTask.id)).where(
            WorkflowTask.status == "COMPLETED"
        )
    )).scalar() or 0

    breached_events = (await db.execute(
        select(func.count(SLAEvent.id)).where(SLAEvent.status == "BREACHED")
    )).scalar() or 0

    on_track = total_tasks - overdue_tasks - completed_tasks
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100, 2)
        breach_rate = round((breached_events / total_tasks) * 100, 2)
    else:
        completion_rate = 0.0
        breach_rate = 0.0

    return {
        "total_tasks": total_tasks,
        "on_track": max(on_track, 0),
        "overdue_tasks": overdue_tasks,
        "completed_tasks": completed_tasks,
        "sla_breaches": breached_events,
        "completion_rate": completion_rate,
        "breach_rate": breach_rate,
    }


async def create_sla_rule(db: AsyncSession, from_status: str, to_status: str,
                          max_duration_hours: int, role_id: UUID = None,
                          priority: int = 3, is_active: bool = True):
    rule = SLARule(
        from_status=from_status,
        to_status=to_status,
        max_duration_hours=max_duration_hours,
        role_id=role_id,
        priority=priority,
        is_active=is_active,
    )
    db.add(rule)
    await db.flush()
    return rule


async def list_sla_rules(db: AsyncSession) -> list:
    result = await db.execute(select(SLARule).order_by(SLARule.priority))
    return result.scalars().all()
