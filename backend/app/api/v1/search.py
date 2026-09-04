from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.security.dependencies import get_db, get_current_user
from app.services.search_service import global_search
from app.models.models import Profile

router = APIRouter()


@router.get("")
async def search(
    query: str = Query(..., min_length=1),
    entity_types: str = Query(None),
    status: str = Query(None),
    state_id: str = Query(None),
    district_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    import uuid
    from typing import Optional
    entities = entity_types.split(",") if entity_types else None
    state = uuid.UUID(state_id) if state_id else None
    district = uuid.UUID(district_id) if district_id else None

    result = await global_search(
        db=db, query_text=query, entity_types=entities,
        status_filter=status, state_id=state, district_id=district,
        page=page, page_size=page_size,
    )
    return {
        "success": True,
        "data": result["data"],
        "total": result["total"],
        "page": page,
        "page_size": page_size,
        "message": "Search completed",
    }
