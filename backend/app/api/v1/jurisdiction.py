from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services import jurisdiction_service
from app.schemas.jurisdiction import JurisdictionConfirm
from app.models.models import Profile

router = APIRouter()


@router.post("/suggest/{project_id}")
async def suggest_jurisdiction(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await jurisdiction_service.suggest_jurisdiction(db, project_id, actor=current_user)
    decision = result.get("decision")
    if decision:
        return {
            "success": True,
            "data": {
                "decision_id": str(decision.id),
                "suggested_appropriate_govt": decision.suggested_appropriate_govt,
                "suggested_acquiring_body": decision.suggested_acquiring_body,
                "suggested_authority": decision.suggested_authority,
                "confidence_score": decision.confidence_score,
                "reason": decision.reason,
                "evaluation": result.get("evaluation"),
            },
            "message": "Jurisdiction suggested",
        }
    return {
        "success": True,
        "data": {"evaluation": result.get("evaluation", {})},
        "message": result.get("message", "No suggestion"),
    }


@router.post("/confirm/{decision_id}")
async def confirm_jurisdiction(
    project_id: UUID = Query(...),
    decision_id: UUID = None,
    data: JurisdictionConfirm = None,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if decision_id is None:
        raise HTTPException(status_code=400, detail="decision_id required in path")
    decision = await jurisdiction_service.confirm_jurisdiction(
        db=db,
        project_id=project_id,
        decision_id=decision_id,
        officer=current_user,
        confirmed=data.confirmed if data else True,
        comment=data.comment if data else None,
        override_appropriate_govt=data.override_appropriate_govt if data else None,
        override_acquiring_body=data.override_acquiring_body if data else None,
    )
    return {
        "success": True,
        "data": {
            "id": str(decision.id),
            "officer_verified": decision.officer_verified,
            "officer_comment": decision.officer_comment,
            "confirmed_at": decision.confirmed_at.isoformat() if decision.confirmed_at else None,
        },
        "message": "Jurisdiction decision confirmed",
    }


@router.get("/rules")
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    rules = await jurisdiction_service.get_active_rules(db)
    return {
        "success": True,
        "data": [
            {
                "id": str(r.id),
                "rule_code": r.rule_code,
                "rule_version": r.rule_version,
                "effective_from": r.effective_from.isoformat() if r.effective_from else None,
                "effective_to": r.effective_to.isoformat() if r.effective_to else None,
                "conditions": r.conditions,
                "result": r.result,
                "source_reference": r.source_reference,
                "is_active": r.is_active,
            }
            for r in rules
        ],
        "message": "Jurisdiction rules retrieved",
    }
