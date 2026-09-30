import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.rag import Document
import app.services.rag as rag_service

logger = logging.getLogger(__name__)


async def list_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    logger.info("documents.list count=%d", len(docs))
    return docs


async def upload_document(
    db: AsyncSession,
    title: str,
    content: str,
    source: str = "upload",
    module_id: uuid.UUID | None = None,
    *,
    commit: bool = True,
) -> Document:
    # Title is validated + sanitized at the HTTP boundary (routers/documents.py
    # via DocumentCreate) before it reaches here, so the INFO logs below are
    # injection-safe (CWE-117). The %r format is a further backstop.
    logger.info(
        "documents.upload title=%r source=%s module_id=%s content_len=%d",
        title,
        source,
        module_id,
        len(content),
    )
    doc = await rag_service.ingest_document(
        db,
        title=title,
        content=content,
        source=source,
        module_id=module_id,
        commit=commit,
    )
    logger.info("documents.upload_ok id=%s title=%r", doc.id, title)
    # Audit row is written by the router (routers/documents.py) where the
    # authenticated user is in scope; writing here too produced a duplicate,
    # mis-attributed (user_id=None) entry per upload.
    return doc


async def delete_document(
    db: AsyncSession, doc_id: uuid.UUID, *, commit: bool = True
) -> None:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        logger.warning("documents.not_found id=%s", doc_id)
        raise NotFoundException
    title = doc.title
    await db.delete(doc)
    if commit:
        await db.commit()
    else:
        await db.flush()
    logger.info("documents.delete id=%s title=%r", doc_id, title)
