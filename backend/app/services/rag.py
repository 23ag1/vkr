import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.llm as llm_service
from app.models.rag import Document, DocumentChunk

logger = logging.getLogger(__name__)

_EMBED_MODEL = "text-embedding-3-small"


def chunk_text(
    text_content: str, max_tokens: int = 500, overlap: int = 50
) -> list[str]:
    words = text_content.split()
    if len(words) <= max_tokens:
        return [text_content]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunks.append(" ".join(words[start:end]))
        start += max_tokens - overlap
    return chunks


async def embed_text(content: str) -> list[float]:
    response = await llm_service.get_client().embeddings.create(
        model=_EMBED_MODEL,
        input=content[:8000],
    )
    return response.data[0].embedding


async def _embed_batch(contents: list[str]) -> list[list[float]]:
    response = await llm_service.get_client().embeddings.create(
        model=_EMBED_MODEL,
        input=[c[:8000] for c in contents],
    )
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


async def ingest_document(
    db: AsyncSession,
    title: str,
    content: str,
    source: str = "",
    module_id=None,
    *,
    commit: bool = True,
) -> Document:
    """Ingest a document + its embedded chunks.

    commit=False keeps doc + chunks in the caller's open transaction (flush only)
    so an audit row can be committed atomically alongside them by the caller.
    """
    doc = Document(title=title, source=source, module_id=module_id)
    db.add(doc)
    # Flush (not commit) to populate doc.id for the chunk FKs without ending the
    # transaction — keeps the whole ingest atomic with the caller's audit row.
    await db.flush()
    await db.refresh(doc)

    chunks = chunk_text(content, max_tokens=500, overlap=50)
    embeddings = await _embed_batch(chunks)
    for idx, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
        db.add(
            DocumentChunk(
                document_id=doc.id,
                content=chunk_content,
                embedding=embedding,
                chunk_index=idx,
            )
        )

    if commit:
        await db.commit()
    else:
        await db.flush()
    logger.info("rag.ingest doc_id=%s chunks=%d", doc.id, len(chunks))
    return doc


async def retrieve_chunks(
    db: AsyncSession, query: str, top_k: int = 5
) -> list[DocumentChunk]:
    query_embedding = await embed_text(query)
    result = await db.execute(
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.op("<=>")(query_embedding))
        .limit(top_k)
    )
    chunks = result.scalars().all()
    logger.info(
        "rag.retrieve query_len=%d top_k=%d found=%d", len(query), top_k, len(chunks)
    )
    return chunks
