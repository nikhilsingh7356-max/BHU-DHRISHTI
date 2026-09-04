import os
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.security.dependencies import get_db, get_current_user
from app.services import document_service
from app.models.models import Profile
from app.core.config import settings

router = APIRouter()


@router.get("/project/{project_id}")
async def list_project_documents(
    project_id: UUID,
    status: str = Query(None),
    document_type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    result = await document_service.list_documents(
        db=db, project_id=project_id, status_filter=status,
        document_type=document_type, page=page, page_size=page_size,
    )
    data = [_doc_to_dict(d) for d in result["data"]]
    return {
        "success": True,
        "data": data,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
        "message": "Documents retrieved",
    }


@router.post("/upload", status_code=201)
async def upload_document(
    project_id: UUID = Form(...),
    document_type: str = Form(...),
    title: str = Form(...),
    parcel_id: UUID = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    checksum = document_service.compute_checksum(content)
    document = await document_service.create_document(
        db=db,
        project_id=project_id,
        parcel_id=parcel_id,
        document_type=document_type,
        title=title,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=current_user.id,
    )

    from app.audit.service import log_action
    await log_action(
        db=db, actor_id=current_user.id, actor_email=current_user.email,
        action="UPLOAD_DOCUMENT", entity_type="document", entity_id=document.id,
        new_value={"file_name": file.filename, "title": title, "checksum": checksum},
    )

    return {
        "success": True,
        "data": _doc_to_dict(document),
        "message": "Document uploaded successfully",
    }


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    document = await document_service.get_document(db, document_id)
    return {
        "success": True,
        "data": _doc_to_dict(document),
        "message": "Document retrieved",
    }


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    document = await document_service.get_document(db, document_id)
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type=document.mime_type,
    )


@router.put("/{document_id}/verify")
async def verify_document(
    document_id: UUID,
    status_to_set: str = Query(...),
    comment: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if status_to_set not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Status must be APPROVED or REJECTED")
    document = await document_service.verify_document(
        db, document_id, current_user, status_to_set, comment
    )
    return {
        "success": True,
        "data": _doc_to_dict(document),
        "message": f"Document {status_to_set.lower()}",
    }


def _doc_to_dict(d):
    return {
        "id": str(d.id),
        "project_id": str(d.project_id),
        "parcel_id": str(d.parcel_id) if d.parcel_id else None,
        "document_type": d.document_type,
        "title": d.title,
        "file_name": d.file_name,
        "file_path": d.file_path,
        "file_size": d.file_size,
        "mime_type": d.mime_type,
        "status": d.status,
        "uploaded_by": str(d.uploaded_by),
        "verified_by": str(d.verified_by) if d.verified_by else None,
        "verification_comment": d.verification_comment,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }
