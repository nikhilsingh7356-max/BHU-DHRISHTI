from fastapi import APIRouter
from app.api.v1 import (
    auth, projects, parcels, documents, workflow, verification,
    compensation, rr, jurisdiction, gis, objections, hearings,
    notifications, audit, reports, admin, search, health,
    intelligence, analytics
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(parcels.router, prefix="/parcels", tags=["parcels"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(compensation.router, prefix="/compensation", tags=["compensation"])
api_router.include_router(rr.router, prefix="/rr", tags=["rr"])
api_router.include_router(jurisdiction.router, prefix="/jurisdiction", tags=["jurisdiction"])
api_router.include_router(gis.router, prefix="/gis", tags=["gis"])
api_router.include_router(objections.router, prefix="/objections", tags=["objections"])
api_router.include_router(hearings.router, prefix="/hearings", tags=["hearings"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
