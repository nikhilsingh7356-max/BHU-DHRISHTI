from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services.search_service import schedule_hearing, list_hearings
from app.schemas.rr import HearingCreate
from app.models.models import Profile

router = APIRouter()


@router.get("/objection/{objection_id}")
async def get_objection_hearings(
    objection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    hearings = await list_hearings(db, objection_id)
    return {
        "success": True,
        "data": [
            {
                "id": str(h.id),
                "objection_id": str(h.objection_id),
                "hearing_date": h.hearing_date.isoformat() if h.hearing_date else None,
                "hearing_officer_id": str(h.hearing_officer_id),
                "location": h.location,
                "decision": h.decision,
                "decision_details": h.decision_details,
                "decision_date": h.decision_date.isoformat() if h.decision_date else None,
                "next_hearing_date": h.next_hearing_date.isoformat() if h.next_hearing_date else None,
            }
            for h in hearings
        ],
        "message": "Hearings retrieved",
    }


@router.post("", status_code=201)
async def schedule_hearing_route(
    data: HearingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    hearing = await schedule_hearing(
        db, data.objection_id, data.hearing_date, current_user.id, data.location
    )
    return {
        "success": True,
        "data": {
            "id": str(hearing.id),
            "objection_id": str(hearing.objection_id),
            "hearing_date": hearing.hearing_date.isoformat(),
            "hearing_officer_id": str(hearing.hearing_officer_id),
            "location": hearing.location,
        },
        "message": "Hearing scheduled",
    }
