from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.models.models import (
    Project, Parcel, ProjectDocument, CompensationCase, RRCase,
    Objection, WorkflowTask, SLAEvent, Profile, ProjectParcel, ParcelOwner
)
from app.services.compensation_service import get_compensation_summary
from app.services.sla_service import get_sla_dashboard
from app.models.models import Profile as ProfileModel

router = APIRouter()


@router.get("/project/{project_id}/summary")
async def project_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    parcels_count = (await db.execute(
        select(func.count(ProjectParcel.id)).where(ProjectParcel.project_id == project_id)
    )).scalar() or 0
    total_area = (await db.execute(
        select(func.coalesce(func.sum(Parcel.area_sq_m), 0))
        .select_from(ProjectParcel)
        .join(Parcel, Parcel.id == ProjectParcel.parcel_id)
        .where(ProjectParcel.project_id == project_id)
    )).scalar() or Decimal("0")
    docs_count = (await db.execute(
        select(func.count(ProjectDocument.id)).where(ProjectDocument.project_id == project_id)
    )).scalar() or 0
    comp_total = (await db.execute(
        select(func.coalesce(func.sum(CompensationCase.total_amount), 0))
        .where(CompensationCase.project_id == project_id)
    )).scalar() or Decimal("0")
    rr_count = (await db.execute(
        select(func.count(RRCase.id)).where(RRCase.project_id == project_id)
    )).scalar() or 0
    obj_count = (await db.execute(
        select(func.count(Objection.id)).where(Objection.project_id == project_id)
    )).scalar() or 0

    return {
        "success": True,
        "data": {
            "project": {
                "id": str(project.id),
                "project_code": project.project_code,
                "name": project.name,
                "status": project.status,
            },
            "total_parcels": parcels_count,
            "total_area_sq_m": float(total_area),
            "total_documents": docs_count,
            "compensation_total": float(comp_total),
            "rr_cases_count": rr_count,
            "objections_count": obj_count,
        },
        "message": "Project summary generated",
    }


@router.get("/compensation-summary")
async def compensation_summary_route(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    summary = await get_compensation_summary(db)
    return {
        "success": True,
        "data": summary,
        "message": "Compensation summary generated",
    }


@router.get("/sla-summary")
async def sla_summary_route(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    summary = await get_sla_dashboard(db)
    return {
        "success": True,
        "data": summary,
        "message": "SLA summary generated",
    }


@router.get("/dashboard-stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    active_projects = (await db.execute(
        select(func.count(Project.id)).where(Project.status.in_([
            "SUBMITTED", "UNDER_REVIEW", "JURISDICTION_CHECK",
            "GIS_VERIFICATION", "PUBLIC_HEARING", "COMPENSATION_ASSESSMENT",
            "RR_PLANNING", "APPROVED", "IN_PROGRESS",
        ]))
    )).scalar() or 0
    completed_projects = (await db.execute(
        select(func.count(Project.id)).where(Project.status == "COMPLETED")
    )).scalar() or 0
    total_parcels = (await db.execute(select(func.count(Parcel.id)))).scalar() or 0
    total_area = (await db.execute(
        select(func.coalesce(func.sum(Parcel.area_sq_m), 0))
    )).scalar() or Decimal("0")
    total_docs = (await db.execute(select(func.count(ProjectDocument.id)))).scalar() or 0
    pending_comp = (await db.execute(
        select(func.count(CompensationCase.id)).where(CompensationCase.status.in_(["ASSESSED", "PENDING_APPROVAL"]))
    )).scalar() or 0
    total_comp = (await db.execute(
        select(func.coalesce(func.sum(CompensationCase.total_amount), 0))
    )).scalar() or Decimal("0")
    open_objs = (await db.execute(
        select(func.count(Objection.id)).where(Objection.status.in_(["SUBMITTED", "UNDER_REVIEW", "HEARING_SCHEDULED"]))
    )).scalar() or 0
    sla_breaches = (await db.execute(
        select(func.count(SLAEvent.id)).where(SLAEvent.status == "BREACHED")
    )).scalar() or 0
    users_count = (await db.execute(select(func.count(ProfileModel.id)))).scalar() or 0

    return {
        "success": True,
        "data": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_parcels": total_parcels,
            "total_area_sq_m": float(total_area),
            "total_documents": total_docs,
            "pending_compensation_cases": pending_comp,
            "total_compensation_amount": float(total_comp),
            "open_objections": open_objs,
            "sla_breaches": sla_breaches,
            "users_count": users_count,
        },
        "message": "Dashboard statistics generated",
    }
