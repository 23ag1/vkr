import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.chat import ChatMessage, ChatSession
from app.models.rag import Document
import app.services.llm as llm_service
import app.services.rag as rag_service
from app.services.prompt_guard import sanitize_user_input

logger = logging.getLogger(__name__)

_MENTOR_SYSTEM = (
    "You are an expert information security mentor. Answer the student's question "
    "using the provided knowledge base context. Be clear, educational, and concise. "
    "Do not include PII."
)

_DEFAULT_TITLES = {"", "New Chat", "Новый чат"}

# Per-message budget for re-fed history. Larger than MAX_USER_INPUT so benign
# long assistant replies keep context fidelity, while still capping each turn.
_HISTORY_MSG_BUDGET = 4000


async def _build_sources(db: AsyncSession, chunks: list) -> dict | None:
    if not chunks:
        return None
    doc_ids = list(dict.fromkeys(c.document_id for c in chunks))
    docs_result = await db.execute(select(Document).where(Document.id.in_(doc_ids)))
    docs_by_id = {d.id: d for d in docs_result.scalars().all()}
    documents = [
        {"id": str(did), "title": docs_by_id[did].title}
        for did in doc_ids
        if did in docs_by_id
    ]
    return {"documents": documents} if documents else None


async def list_sessions(db: AsyncSession, user_id: uuid.UUID) -> list[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = result.scalars().all()
    logger.info("mentor.list_sessions user_id=%s count=%d", user_id, len(sessions))
    return sessions


async def create_session(
    db: AsyncSession, user_id: uuid.UUID, title: str = "New Chat", module_id=None
) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title, module_id=module_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(
        "mentor.create_session id=%s user_id=%s module_id=%s",
        session.id,
        user_id,
        module_id,
    )
    return session


async def list_messages(db: AsyncSession, session_id: uuid.UUID) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    logger.info(
        "mentor.list_messages session_id=%s count=%d", session_id, len(messages)
    )
    return messages


async def send_message(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID, content: str
) -> ChatMessage:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None or session.user_id != user_id:
        logger.warning(
            "mentor.send_unauthorized session_id=%s user_id=%s", session_id, user_id
        )
        raise NotFoundException

    content = sanitize_user_input(content)
    logger.info(
        "mentor.send session_id=%s user_id=%s msg_len=%d",
        session_id,
        user_id,
        len(content),
    )

    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    await db.commit()

    history = await list_messages(db, session_id)
    last_10 = history[-10:]

    # Auto-title the session from the first user message (like ChatGPT history).
    if len(history) == 1 and (session.title or "").strip() in _DEFAULT_TITLES:
        session.title = content[:60].strip() + ("…" if len(content) > 60 else "")
        await db.commit()
        logger.info(
            "mentor.auto_title session_id=%s title=%r", session_id, session.title
        )

    chunks = await rag_service.retrieve_chunks(db, query=content, top_k=5)
    # RAG chunk text is admin-uploaded document content and is injected verbatim
    # into the LLM 'Knowledge base' system message — same prompt-injection class
    # as vkr-s3v/vkr-f2l. Sanitize each chunk before truncating to the 500-char
    # budget (sanitize-then-slice so a stripped pattern can't straddle the cut).
    context = "\n".join(f"- {sanitize_user_input(c.content)[:500]}" for c in chunks)
    logger.info("mentor.rag_retrieved session_id=%s chunks=%d", session_id, len(chunks))

    sources = await _build_sources(db, chunks)

    messages = [{"role": "system", "content": _MENTOR_SYSTEM}]
    if context:
        messages.append({"role": "system", "content": f"Knowledge base:\n{context}"})
    # Re-fed chat history is untrusted at prompt-construction: role=assistant is
    # GPT-4o output stored verbatim (an indirect-injection loop — a poisoned reply
    # re-executes on later turns) and role=user may predate sanitize-at-write.
    # Sanitize each message before it reaches GPT-4o (vkr-x0o; ADR vkr-33c).
    for msg in last_10:
        clean = sanitize_user_input(msg.content, max_len=_HISTORY_MSG_BUDGET)
        messages.append({"role": msg.role, "content": clean})

    reply_text = await llm_service.chat_completion(messages, temperature=0.5)
    logger.info(
        "mentor.reply_ok session_id=%s reply_len=%d", session_id, len(reply_text)
    )

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=reply_text,
        sources=sources,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    return assistant_msg
