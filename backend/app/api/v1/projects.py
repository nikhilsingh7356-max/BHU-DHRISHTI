from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import project_service
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectSubmit, ProjectFilters
)
from app.models.models import Profile
from app.schemas.auth import SuccessResponse, ErrorResponse

router = APIRouter()


@router.get("")
async def list_projects(
    status: str = Query(None),
    state_id: UUID = Query(None),
    district_id: UUID = Query(None),
    project_type: str = Query(None),
    search: str = Query(None),
    priority: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await project_service.list_projects(
        db=db,
        status_filter=status,
        state_id=state_id,
        district_id=district_id,
        project_type=project_type,
        search=search,
        priority=priority,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    data = []
    for p in result["data"]:
        data.append(_project_to_dict(p))
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Projects retrieved",
    }


@router.post("", status_code=201)
async def create_project(
    data: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    project = await project_service.create_project(
        db=db, data=data, user=current_user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "data": _project_to_dict(project),
        "message": "Project created successfully",
    }


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    project = await project_service.get_project(db, project_id)
    d = _project_to_dict(project)
    d["status_history"] = [
        {
            "id": str(h.id),
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "changed_by": str(h.changed_by),
            "comment": h.comment,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
        }
        for h in (project.status_history or [])
    ]
    d["parcels_count"] = len(project.parcels or [])
    d["documents_count"] = len(project.documents or [])
    d["compensation_cases_count"] = len(project.compensation_cases or [])
    d["rr_cases_count"] = len(project.rr_cases or [])
    d["objections_count"] = len(project.objections or [])
    return {
        "success": True,
        "data": d,
        "message": "Project retrieved",
    }


@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    project = await project_service.update_project(
        db, project_id, data, current_user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "data": _project_to_dict(project),
        "message": "Project updated successfully",
    }


@router.post("/{project_id}/submit")
async def submit_project(
    project_id: UUID,
    request: Request,
    data: Optional[ProjectSubmit] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    project = await project_service.submit_project(
        db, project_id, current_user, data.comment if data else None,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "data": _project_to_dict(project),
        "message": "Project submitted for review",
    }


@router.get("/{project_id}/timeline")
async def get_project_timeline(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    history = await project_service.get_project_timeline(db, project_id)
    return {
        "success": True,
        "data": [
            {
                "id": str(h.id),
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "changed_by": str(h.changed_by),
                "comment": h.comment,
                "changed_at": h.changed_at.isoformat() if h.changed_at else None,
            }
            for h in history
        ],
        "message": "Project timeline retrieved",
    }


@router.get("/{project_id}/activity")
async def get_project_activity(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await project_service.get_project_activity(db, project_id, page, page_size)
    activities = []
    for a in result["data"]:
        activities.append({
            "id": str(a.id),
            "project_id": str(a.project_id),
            "actor_id": str(a.actor_id),
            "activity_type": a.activity_type,
            "description": a.description,
            "metadata": a.meta,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return {
        "success": True,
        "data": activities,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Project activity retrieved",
    }


def _project_to_dict(p):
    return {
        "id": str(p.id),
        "project_code": p.project_code,
        "name": p.name,
        "description": p.description,
        "project_type": p.project_type,
        "purpose": p.purpose,
        "public_category": p.public_category,
        "sponsor_id": str(p.sponsor_id) if p.sponsor_id else None,
        "land_requiring_body_id": str(p.land_requiring_body_id) if p.land_requiring_body_id else None,
        "proposed_area_sq_m": float(p.proposed_area_sq_m) if p.proposed_area_sq_m else None,
        "state_id": str(p.state_id) if p.state_id else None,
        "district_id": str(p.district_id) if p.district_id else None,
        "tehsil_id": str(p.tehsil_id) if p.tehsil_id else None,
        "village_id": str(p.village_id) if p.village_id else None,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "target_completion_date": p.target_completion_date.isoformat() if p.target_completion_date else None,
        "priority": p.priority,
        "estimated_cost": float(p.estimated_cost) if p.estimated_cost else None,
        "funding_source": p.funding_source,
        "status": p.status,
        "created_by": str(p.created_by),
        "version": p.version,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
