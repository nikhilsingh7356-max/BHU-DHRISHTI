from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc, asc, update
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status
from app.models.models import (
    Project, ProjectStatusHistory, WorkflowInstance, ProjectActivity,
    Profile, State, District, Tehsil, Village, Parcel, ProjectParcel,
    ProjectDocument, JurisdictionDecision, CompensationCase, RRCase,
    Objection, AuditLog, Notification
)
from app.audit.service import log_action


async def generate_project_code(db: AsyncSession) -> str:
    current_year = datetime.utcnow().year
    prefix = f"BD-{current_year}-"
    result = await db.execute(
        select(func.count(Project.id)).where(Project.project_code.like(f"{prefix}%"))
    )
    count = result.scalar() or 0
    return f"{prefix}{count + 1:05d}"


async def create_project(
    db: AsyncSession,
    data,
    user: Profile,
    ip: str = None,
    user_agent: str = None,
) -> Project:
    project_code = await generate_project_code(db)
    project = Project(
        project_code=project_code,
        name=data.name,
        description=data.description,
        project_type=data.project_type,
        purpose=data.purpose,
        public_category=data.public_category,
        sponsor_id=data.sponsor_id,
        land_requiring_body_id=data.land_requiring_body_id,
        proposed_area_sq_m=data.proposed_area_sq_m,
        state_id=data.state_id,
        district_id=data.district_id,
        tehsil_id=data.tehsil_id,
        village_id=data.village_id,
        start_date=data.start_date,
        target_completion_date=data.target_completion_date,
        priority=data.priority,
        estimated_cost=data.estimated_cost,
        funding_source=data.funding_source,
        status="DRAFT",
        created_by=user.id,
        version=1,
    )
    db.add(project)
    await db.flush()

    workflow_instance = WorkflowInstance(
        project_id=project.id,
        current_status="DRAFT",
    )
    db.add(workflow_instance)

    history = ProjectStatusHistory(
        project_id=project.id,
        previous_status=None,
        new_status="DRAFT",
        changed_by=user.id,
        comment="Project created",
    )
    db.add(history)

    activity = ProjectActivity(
        project_id=project.id,
        actor_id=user.id,
        activity_type="PROJECT_CREATED",
        description=f"Project {project.name} created with code {project.project_code}",
        meta={"project_code": project_code},
    )
    db.add(activity)

    await db.flush()

    await log_action(
        db=db,
        actor_id=user.id,
        actor_email=user.email,
        action="CREATE_PROJECT",
        entity_type="project",
        entity_id=project.id,
        new_value={
            "project_code": project_code,
            "name": data.name,
            "project_type": data.project_type,
        },
        ip_address=ip,
        user_agent=user_agent,
    )
    return project


async def list_projects(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    state_id: Optional[UUID] = None,
    district_id: Optional[UUID] = None,
    project_type: Optional[str] = None,
    search: Optional[str] = None,
    priority: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    query = select(Project).options(
        selectinload(Project.creator),
        selectinload(Project.workflow_instance),
    )
    count_query = select(func.count(Project.id))

    conditions = []
    if status_filter:
        conditions.append(Project.status == status_filter)
    if state_id:
        conditions.append(Project.state_id == state_id)
    if district_id:
        conditions.append(Project.district_id == district_id)
    if project_type:
        conditions.append(Project.project_type == project_type)
    if priority:
        conditions.append(Project.priority == priority)
    if search:
        like = f"%{search}%"
        conditions.append(or_(
            Project.name.ilike(like),
            Project.project_code.ilike(like),
            Project.description.ilike(like),
        ))

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar() or 0

    sort_col = {
        "created_at": Project.created_at,
        "name": Project.name,
        "project_code": Project.project_code,
        "status": Project.status,
        "priority": Project.priority,
        "updated_at": Project.updated_at,
        "estimated_cost": Project.estimated_cost,
    }.get(sort_by, Project.created_at)

    if sort_order == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    projects = result.scalars().unique().all()

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "data": projects,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def get_project(db: AsyncSession, project_id: UUID) -> Project:
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.creator),
            selectinload(Project.workflow_instance).selectinload(WorkflowInstance.tasks),
            selectinload(Project.workflow_instance).selectinload(WorkflowInstance.transitions),
            selectinload(Project.status_history),
            selectinload(Project.documents),
            selectinload(Project.sponsor),
            selectinload(Project.land_requiring_body),
            selectinload(Project.jurisdiction_decisions),
            selectinload(Project.gis_verifications),
            selectinload(Project.compensation_cases),
            selectinload(Project.rr_cases),
            selectinload(Project.objections),
            selectinload(Project.activity),
            selectinload(Project.parcels),
        )
        .where(Project.id == project_id)
    )
    project = result.scalars().unique().first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


async def update_project(
    db: AsyncSession,
    project_id: UUID,
    data,
    user: Profile,
    ip: str = None,
    user_agent: str = None,
) -> Project:
    project = await get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    old_values = {
        "name": project.name,
        "status": project.status,
        "project_type": project.project_type,
    }

    update_fields = {}
    if data.name is not None:
        project.name = data.name
        update_fields["name"] = data.name
    if data.description is not None:
        project.description = data.description
        update_fields["description"] = data.description
    if data.project_type is not None:
        project.project_type = data.project_type
        update_fields["project_type"] = data.project_type
    if data.purpose is not None:
        project.purpose = data.purpose
        update_fields["purpose"] = data.purpose
    if data.public_category is not None:
        project.public_category = data.public_category
        update_fields["public_category"] = data.public_category
    if data.sponsor_id is not None:
        project.sponsor_id = data.sponsor_id
        update_fields["sponsor_id"] = str(data.sponsor_id)
    if data.land_requiring_body_id is not None:
        project.land_requiring_body_id = data.land_requiring_body_id
        update_fields["land_requiring_body_id"] = str(data.land_requiring_body_id)
    if data.proposed_area_sq_m is not None:
        project.proposed_area_sq_m = data.proposed_area_sq_m
        update_fields["proposed_area_sq_m"] = str(data.proposed_area_sq_m)
    if data.state_id is not None:
        project.state_id = data.state_id
        update_fields["state_id"] = str(data.state_id)
    if data.district_id is not None:
        project.district_id = data.district_id
        update_fields["district_id"] = str(data.district_id)
    if data.tehsil_id is not None:
        project.tehsil_id = data.tehsil_id
        update_fields["tehsil_id"] = str(data.tehsil_id)
    if data.village_id is not None:
        project.village_id = data.village_id
        update_fields["village_id"] = str(data.village_id)
    if data.start_date is not None:
        project.start_date = data.start_date
        update_fields["start_date"] = str(data.start_date)
    if data.target_completion_date is not None:
        project.target_completion_date = data.target_completion_date
        update_fields["target_completion_date"] = str(data.target_completion_date)
    if data.priority is not None:
        project.priority = data.priority
        update_fields["priority"] = data.priority
    if data.estimated_cost is not None:
        project.estimated_cost = data.estimated_cost
        update_fields["estimated_cost"] = str(data.estimated_cost)
    if data.funding_source is not None:
        project.funding_source = data.funding_source
        update_fields["funding_source"] = data.funding_source

    project.version += 1
    project.updated_at = datetime.utcnow()

    activity = ProjectActivity(
        project_id=project.id,
        actor_id=user.id,
        activity_type="PROJECT_UPDATED",
        description=f"Project {project.name} updated (version {project.version})",
        meta=update_fields,
    )
    db.add(activity)

    await db.flush()

    await log_action(
        db=db,
        actor_id=user.id,
        actor_email=user.email,
        action="UPDATE_PROJECT",
        entity_type="project",
        entity_id=project.id,
        previous_value=old_values,
        new_value=update_fields,
        ip_address=ip,
        user_agent=user_agent,
    )
    return project


async def submit_project(
    db: AsyncSession,
    project_id: UUID,
    user: Profile,
    comment: Optional[str] = None,
    ip: str = None,
    user_agent: str = None,
) -> Project:
    project = await get_project(db, project_id)
    if project.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT projects can be submitted",
        )
    previous = project.status
    project.status = "SUBMITTED"
    project.updated_at = datetime.utcnow()

    instance = project.workflow_instance
    if instance:
        instance.current_status = "SUBMITTED"
        instance.updated_at = datetime.utcnow()

    history = ProjectStatusHistory(
        project_id=project.id,
        previous_status=previous,
        new_status="SUBMITTED",
        changed_by=user.id,
        comment=comment or "Project submitted for review",
    )
    db.add(history)

    activity = ProjectActivity(
        project_id=project.id,
        actor_id=user.id,
        activity_type="PROJECT_SUBMITTED",
        description=f"Project {project.name} submitted for review",
        meta={"comment": comment},
    )
    db.add(activity)

    await db.flush()

    await log_action(
        db=db,
        actor_id=user.id,
        actor_email=user.email,
        action="SUBMIT_PROJECT",
        entity_type="project",
        entity_id=project.id,
        previous_value={"status": previous},
        new_value={"status": "SUBMITTED"},
        ip_address=ip,
        user_agent=user_agent,
    )
    return project


async def get_project_timeline(db: AsyncSession, project_id: UUID) -> list:
    result = await db.execute(
        select(ProjectStatusHistory)
        .where(ProjectStatusHistory.project_id == project_id)
        .order_by(ProjectStatusHistory.changed_at)
    )
    return result.scalars().all()


async def get_project_activity(db: AsyncSession, project_id: UUID, page: int = 1, page_size: int = 20) -> dict:
    query = select(ProjectActivity).where(ProjectActivity.project_id == project_id)
    count_query = select(func.count(ProjectActivity.id)).where(ProjectActivity.project_id == project_id)
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(desc(ProjectActivity.created_at))
        .offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "data": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
