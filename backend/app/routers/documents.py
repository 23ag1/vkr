import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.documents as documents_service
from app.deps import get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, ok
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter()

_privileged = Depends(require_role("admin", "security_specialist"))


@router.get(
    "", response_model=ApiResponse[list[DocumentResponse]], dependencies=[_privileged]
)
async def list_documents(db: AsyncSession = Depends(get_db)):
    docs = await documents_service.list_documents(db)
    return ok([DocumentResponse.model_validate(d) for d in docs])


@router.post(
    "/upload",
    response_model=ApiResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    module_id: uuid.UUID | None = Form(None),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    # Validate the title at the HTTP boundary so a bad title is a clean 422, not
    # a 500 from the service-layer safety net (max_length + control-char strip).
    try:
        title = DocumentCreate(title=title).title
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid document title",
        ) from exc

    content = (await file.read()).decode("utf-8", errors="replace")
    doc = await documents_service.upload_document(
        db,
        title=title,
        content=content,
        source=file.filename or "upload",
        module_id=module_id,
        commit=False,
    )
    await audit_service.write(
        db,
        user_id=current_user.id,
        action="document_uploaded",
        details={"document_id": str(doc.id), "title": doc.title},
        commit=False,
    )
    # Single atomic commit: the document, its chunks, and the audit row persist
    # together or not at all (no crash-gap where the doc exists without an audit).
    await db.commit()
    return ok(DocumentResponse.model_validate(doc))


@router.delete("/{doc_id}", response_model=ApiResponse[None])
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    await documents_service.delete_document(db, doc_id, commit=False)
    await audit_service.write(
        db,
        user_id=current_user.id,
        action="document_deleted",
        details={"document_id": str(doc_id)},
        commit=False,
    )
    # Single atomic commit: the deletion and its audit row are one transaction.
    await db.commit()
    return ok(None)
