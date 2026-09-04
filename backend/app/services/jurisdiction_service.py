from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status
from app.models.models import (
    Project, JurisdictionRule, JurisdictionDecision, ProjectActivity, Profile
)
from app.jurisdiction.engine import evaluate_jurisdiction_rules
from app.audit.service import log_action


async def suggest_jurisdiction(db: AsyncSession, project_id: UUID, actor: Profile = None) -> dict:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(JurisdictionRule).where(
            JurisdictionRule.is_active == True,  # noqa: E712
            JurisdictionRule.effective_from <= datetime.utcnow(),
            or_(
                JurisdictionRule.effective_to.is_(None),
                JurisdictionRule.effective_to >= datetime.utcnow(),
            )
        )
    )
    rules = result.scalars().all()

    if not rules:
        return {
            "success": True,
            "decision": None,
            "message": "No active jurisdiction rules found",
        }

    evaluation = evaluate_jurisdiction_rules(rules, project, db)

    if not evaluation.get("rule_id"):
        activity = ProjectActivity(
            project_id=project.id,
            actor_id=actor.id if actor else None,
            activity_type="JURISDICTION_SUGGESTED",
            description="Jurisdiction evaluation completed (no rule matched)",
            meta=evaluation,
        )
        db.add(activity)
        await db.flush()
        return {
            "success": True,
            "decision": None,
            "evaluation": evaluation,
            "message": evaluation.get("reason", "No jurisdiction rule matched"),
        }

    decision = JurisdictionDecision(
        project_id=project.id,
        rule_id=UUID(evaluation["rule_id"]),
        suggested_appropriate_govt=evaluation["appropriate_govt"],
        suggested_acquiring_body=evaluation["acquiring_body"],
        suggested_authority=evaluation["authority"],
        confidence_score=evaluation["confidence"],
        reason=evaluation["reason"],
    )
    db.add(decision)
    await db.flush()

    activity = ProjectActivity(
        project_id=project.id,
        actor_id=actor.id if actor else None,
        activity_type="JURISDICTION_SUGGESTED",
        description=f"Jurisdiction suggested: {evaluation['authority']}",
        meta=evaluation,
    )
    db.add(activity)
    await db.flush()

    if actor:
        await log_action(
            db=db, actor_id=actor.id, actor_email=actor.email,
            action="JURISDICTION_SUGGESTED", entity_type="project",
            entity_id=project.id,
            new_value={"authority": evaluation["authority"], "confidence": evaluation["confidence"]},
        )

    return {
        "success": True,
        "decision": decision,
        "evaluation": evaluation,
    }


async def confirm_jurisdiction(
    db: AsyncSession,
    project_id: UUID,
    decision_id: UUID,
    officer: Profile,
    confirmed: bool,
    comment: Optional[str] = None,
    override_appropriate_govt: Optional[str] = None,
    override_acquiring_body: Optional[str] = None,
) -> JurisdictionDecision:
    result = await db.execute(
        select(JurisdictionDecision).where(
            JurisdictionDecision.id == decision_id,
            JurisdictionDecision.project_id == project_id,
        )
    )
    decision = result.scalar_one_or_none()
    if decision is None:
        raise HTTPException(status_code=404, detail="Jurisdiction decision not found")

    if override_appropriate_govt:
        decision.suggested_appropriate_govt = override_appropriate_govt
    if override_acquiring_body:
        decision.suggested_acquiring_body = override_acquiring_body

    decision.officer_verified = confirmed
    decision.officer_id = officer.id
    decision.officer_comment = comment
    decision.confirmed_at = datetime.utcnow()

    await db.flush()

    await log_action(
        db=db, actor_id=officer.id, actor_email=officer.email,
        action="CONFIRM_JURISDICTION", entity_type="jurisdiction_decision",
        entity_id=decision.id,
        previous_value={"officer_verified": False},
        new_value={"officer_verified": confirmed, "comment": comment},
    )
    return decision


async def get_active_rules(db: AsyncSession) -> list:
    result = await db.execute(
        select(JurisdictionRule).where(
            JurisdictionRule.is_active == True  # noqa: E712
        ).order_by(JurisdictionRule.rule_code)
    )
    return result.scalars().all()


async def create_jurisdiction_rule(db: AsyncSession, data, actor: Profile) -> JurisdictionRule:
    rule = JurisdictionRule(
        rule_code=data["rule_code"],
        rule_version=data.get("rule_version", "1.0"),
        effective_from=data.get("effective_from") or datetime.utcnow(),
        effective_to=data.get("effective_to"),
        conditions=data.get("conditions", {}),
        result=data.get("result", {}),
        source_reference=data.get("source_reference"),
        is_active=data.get("is_active", True),
    )
    db.add(rule)
    await db.flush()

    await log_action(
        db=db, actor_id=actor.id, actor_email=actor.email,
        action="CREATE_JURISDICTION_RULE", entity_type="jurisdiction_rule",
        entity_id=rule.id, new_value=data,
    )
    return rule
