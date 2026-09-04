from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services.search_service import create_objection, list_objections
from app.schemas.rr import ObjectionCreate
from app.models.models import Profile
from fastapi import Request

router = APIRouter()


@router.get("/project/{project_id}")
async def get_project_objections(
    project_id: UUID,
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await list_objections(
        db=db, project_id=project_id, status_filter=status,
        page=page, page_size=page_size,
    )
    return {
        "success": True,
        "data": result["data"],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Objections retrieved",
    }


@router.post("", status_code=201)
async def create_objection_route(
    data: ObjectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    objection = await create_objection(db, data, current_user)
    return {
        "success": True,
        "data": {
            "id": str(objection.id),
            "objection_code": objection.objection_code,
            "project_id": str(objection.project_id),
            "category": objection.category,
            "status": objection.status,
        },
        "message": "Objection filed successfully",
    }
