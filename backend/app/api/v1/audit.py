import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.security.dependencies import get_db, get_current_user
from app.services.audit_service import get_audit_logs
from app.models.models import Profile

router = APIRouter()


@router.get("")
async def list_audit_logs(
    action: str = Query(None),
    entity_type: str = Query(None),
    entity_id: UUID = Query(None),
    actor_id: UUID = Query(None),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await get_audit_logs(
        db=db, action=action, entity_type=entity_type,
        entity_id=entity_id, actor_id=actor_id,
        start_date=start_date, end_date=end_date,
        page=page, page_size=page_size,
    )
    data = [
        {
            "id": str(l.id),
            "actor_id": str(l.actor_id) if l.actor_id else None,
            "actor_email": l.actor_email,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": str(l.entity_id) if l.entity_id else None,
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in result["data"]
    ]
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Audit logs retrieved",
    }


@router.get("/export")
async def export_audit_logs(
    action: str = Query(None),
    entity_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await get_audit_logs(
        db=db, action=action, entity_type=entity_type,
        page=1, page_size=10000,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "timestamp", "actor_email", "action", "entity_type",
        "entity_id", "ip_address", "metadata"
    ])
    for l in result["data"]:
        writer.writerow([
            str(l.id),
            l.created_at.isoformat() if l.created_at else "",
            l.actor_email or "",
            l.action,
            l.entity_type,
            str(l.entity_id) if l.entity_id else "",
            l.ip_address or "",
            str(l.meta or ""),
        ])

    output.seek(0)
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
