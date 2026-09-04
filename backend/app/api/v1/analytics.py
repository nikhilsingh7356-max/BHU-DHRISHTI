from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.models.models import (
    Profile, HistoricalAnalytics, IntegrationHealth, DataProvenance, WhatIfScenario, Project,
)

router = APIRouter()


def _dict(obj, fields):
    out = {}
    for f in fields:
        v = getattr(obj, f, None)
        if isinstance(v, UUID):
            out[f] = str(v)
        else:
            out[f] = v
    return out


# --------------------------------------------------------------------------
# Historical analytics
# --------------------------------------------------------------------------
@router.get("/historical")
async def list_historical(
    metric_name: str = Query(None),
    entity_type: str = Query(None),
    period: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(HistoricalAnalytics).order_by(HistoricalAnalytics.period)
    if metric_name:
        q = q.where(HistoricalAnalytics.metric_name == metric_name)
    if entity_type:
        q = q.where(HistoricalAnalytics.entity_type == entity_type)
    if period:
        q = q.where(HistoricalAnalytics.period == period)
    rows = (await db.execute(q)).scalars().all()
    data = [_dict(r, ["id", "period", "entity_type", "entity_name", "metric_name", "metric_value", "is_demo"]) for r in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Historical analytics retrieved"}


@router.get("/historical/states")
async def state_performance(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    rows = (await db.execute(
        select(HistoricalAnalytics.entity_name, func.avg(HistoricalAnalytics.metric_value).label("avg"))
        .where(HistoricalAnalytics.entity_type == "STATE", HistoricalAnalytics.metric_name == "STATE_PERFORMANCE")
        .group_by(HistoricalAnalytics.entity_name)
    )).all()
    data = [{"state": name, "avg_performance": round(float(v or 0), 1)} for name, v in rows]
    return {"success": True, "data": data, "total": len(data), "message": "State performance retrieved"}


@router.get("/historical/bottlenecks")
async def bottleneck_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    rows = (await db.execute(
        select(HistoricalAnalytics.entity_name, func.sum(HistoricalAnalytics.metric_value).label("total"))
        .where(HistoricalAnalytics.entity_type == "DISTRICT", HistoricalAnalytics.metric_name == "BOTTLENECK_FREQUENCY")
        .group_by(HistoricalAnalytics.entity_name)
    )).all()
    data = [{"district": name, "bottleneck_count": int(total or 0)} for name, total in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Bottleneck analytics retrieved"}


# --------------------------------------------------------------------------
# Integration health
# --------------------------------------------------------------------------
@router.get("/integrations")
async def list_integrations(
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(IntegrationHealth)
    if status:
        q = q.where(IntegrationHealth.status == status)
    rows = (await db.execute(q)).scalars().all()
    data = [_dict(r, ["id", "system_name", "system_code", "integration_type", "last_sync", "status",
                      "records_synced", "failed_records", "conflicts", "api_response_time_ms",
                      "last_error", "is_demo"]) for r in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Integrations retrieved"}


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------
@router.get("/provenance")
async def list_provenance(
    entity_type: str = Query(None),
    source_system: str = Query(None),
    entity_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(DataProvenance)
    if entity_type:
        q = q.where(DataProvenance.entity_type == entity_type)
    if source_system:
        q = q.where(DataProvenance.source_system == source_system)
    if entity_id:
        q = q.where(DataProvenance.entity_id == entity_id)
    rows = (await db.execute(q.order_by(DataProvenance.creation_timestamp.desc()))).scalars().all()
    data = [_dict(r, ["id", "entity_type", "entity_id", "source_system", "source_record_id",
                      "created_by_name", "last_updated", "verification_status", "last_synchronization",
                      "supporting_document", "is_demo"]) for r in rows]
    return {"success": True, "data": data, "total": len(data), "message": "Provenance retrieved"}


# --------------------------------------------------------------------------
# What-if scenarios
# --------------------------------------------------------------------------
@router.get("/whatif")
async def list_whatif(
    project_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    q = select(WhatIfScenario, Project.project_code, Project.name) \
        .join(Project, Project.id == WhatIfScenario.project_id)
    if project_id:
        q = q.where(WhatIfScenario.project_id == project_id)
    rows = (await db.execute(q)).all()
    data = [{"id": str(w.id), "scenario_code": w.scenario_code, "project_id": str(w.project_id),
             "project_code": code, "project_name": name, "title": w.title, "description": w.description,
             "current_completion_label": w.current_completion_label,
             "simulated_completion_label": w.simulated_completion_label,
             "estimated_time_saved_days": w.estimated_time_saved_days, "intervention": w.intervention,
             "assumptions": w.assumptions, "is_demo": w.is_demo}
            for w, code, name in rows]
    return {"success": True, "data": data, "total": len(data), "message": "What-if scenarios retrieved"}
