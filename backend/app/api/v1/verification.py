from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.models.models import ProjectVerification, Project, Profile
from app.audit.service import log_action

router = APIRouter()


@router.get("/project/{project_id}")
async def get_project_verifications(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await db.execute(
        select(ProjectVerification)
        .where(ProjectVerification.project_id == project_id)
        .order_by(desc(ProjectVerification.verified_at))
    )
    items = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(v.id),
                "project_id": str(v.project_id),
                "verifier_id": str(v.verifier_id),
                "verification_type": v.verification_type,
                "status": v.status,
                "comment": v.comment,
                "verified_at": v.verified_at.isoformat() if v.verified_at else None,
            }
            for v in items
        ],
        "total": len(items),
        "message": "Project verifications retrieved",
    }


@router.post("/project/{project_id}/verify", status_code=201)
async def create_verification(
    project_id: UUID,
    verification_type: str = Query(...),
    status: str = Query(...),
    comment: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    verification = ProjectVerification(
        project_id=project_id,
        verifier_id=current_user.id,
        verification_type=verification_type,
        status=status,
        comment=comment,
    )
    db.add(verification)
    await db.flush()

    await log_action(
        db=db, actor_id=current_user.id, actor_email=current_user.email,
        action="CREATE_VERIFICATION", entity_type="project_verification",
        entity_id=verification.id,
        new_value={"verification_type": verification_type, "status": status},
    )

    return {
        "success": True,
        "data": {
            "id": str(verification.id),
            "project_id": str(project_id),
            "verification_type": verification_type,
            "status": status,
            "comment": comment,
        },
        "message": "Verification recorded",
    }
