import hashlib
import os
from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException, status
from app.models.models import ProjectDocument, DocumentVerification, Profile, Project
from app.audit.service import log_action


def compute_checksum(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


async def create_document(
    db: AsyncSession,
    project_id: UUID,
    parcel_id: Optional[UUID],
    document_type: str,
    title: str,
    file_name: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    uploaded_by: UUID,
) -> ProjectDocument:
    result = await db.execute(select(Project).where(Project.id == project_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    document = ProjectDocument(
        project_id=project_id,
        parcel_id=parcel_id,
        document_type=document_type,
        title=title,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        status="PENDING",
        uploaded_by=uploaded_by,
    )
    db.add(document)
    await db.flush()
    return document


async def list_documents(
    db: AsyncSession,
    project_id: UUID = None,
    status_filter: Optional[str] = None,
    document_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(ProjectDocument)
    count_query = select(func.count(ProjectDocument.id))

    if project_id:
        query = query.where(ProjectDocument.project_id == project_id)
        count_query = count_query.where(ProjectDocument.project_id == project_id)
    if status_filter:
        query = query.where(ProjectDocument.status == status_filter)
        count_query = count_query.where(ProjectDocument.status == status_filter)
    if document_type:
        query = query.where(ProjectDocument.document_type == document_type)
        count_query = count_query.where(ProjectDocument.document_type == document_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(desc(ProjectDocument.created_at))
        .offset((page - 1) * page_size).limit(page_size)
    )
    docs = result.scalars().all()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "data": docs, "total": total, "page": page,
        "page_size": page_size, "total_pages": total_pages,
    }


async def get_document(db: AsyncSession, document_id: UUID) -> ProjectDocument:
    result = await db.execute(
        select(ProjectDocument).where(ProjectDocument.id == document_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


async def verify_document(
    db: AsyncSession,
    document_id: UUID,
    verifier: Profile,
    new_status: str,
    comment: Optional[str] = None,
) -> ProjectDocument:
    document = await get_document(db, document_id)

    document.status = new_status
    document.verified_by = verifier.id
    document.verification_comment = comment
    document.updated_at = datetime.utcnow()

    verification = DocumentVerification(
        document_id=document_id,
        verifier_id=verifier.id,
        status=new_status,
        comment=comment,
    )
    db.add(verification)
    await db.flush()

    await log_action(
        db=db, actor_id=verifier.id, actor_email=verifier.email,
        action="VERIFY_DOCUMENT", entity_type="document", entity_id=document.id,
        previous_value={"status": "PENDING"},
        new_value={"status": new_status, "comment": comment},
    )
    return document
