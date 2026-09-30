"""Adaptive initial diagnostic service (ВКР Сценарий 1).

Flow:
  POST /api/diagnostic/start  → creates DiagnosticSession, returns first question
  POST /api/diagnostic/answer → scores answer, returns next question or finishes
  POST /api/diagnostic/finish → (called internally on answer #10) saves profile + auto-assigns

Topic selection is adaptive: weakest-scoring topic is preferred for the next question.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.learning as learning_service
import app.services.llm as llm_service
from app.models.diagnostic import DiagnosticSession, UserCompetencyProfile
from app.models.module import Module
from app.models.test import Question
from app.models.user import User

logger = logging.getLogger(__name__)

TOPICS = ["phishing", "passwords", "pii", "incident_response", "social_engineering"]

MAX_QUESTIONS = 10
WEAK_THRESHOLD = 0.5

_TOPIC_CONTENT = {
    "phishing": (
        "Фишинг и социальная инженерия. "
        "Признаки фишинговых писем: срочность, подозрительный адрес, просьба ввести пароль. "
        "Виды: email-фишинг, спир-фишинг, смишинг, вишинг. Методы защиты: проверка URL, MFA, отчётность."
    ),
    "passwords": (
        "Парольная политика. Требования: длина >= 12, заглавные/строчные/цифры/спецсимволы, "
        "уникальный для каждого сервиса. Запрещено: простые пароли, повторное использование. "
        "Инструменты: менеджеры паролей, MFA."
    ),
    "pii": (
        "Персональные данные (ФЗ-152). Что является ПДн: ФИО, паспорт, биометрия, СНИЛС. "
        "Правила обработки: согласие субъекта, минимизация, хранение внутри РФ. "
        "Ответственность за нарушения."
    ),
    "incident_response": (
        "Реагирование на инциденты ИБ. Классификация: P1 (критический), P2 (высокий), P3 (средний). "
        "Шаги: локализация, сбор доказательств, устранение, восстановление, документирование. "
        "Кому сообщать об инциденте, сроки реагирования."
    ),
    "social_engineering": (
        "Социальная инженерия. Методы: претекстинг, приманка, троян помощи, quid pro quo. "
        "Признаки атаки: необычная просьба, срочность, авторитетный источник. "
        "Правило: никогда не давать данные по телефону без верификации."
    ),
}

# Maps topic → module title keyword for auto-assign
_TOPIC_MODULE_KEYWORDS = {
    "phishing": "фишинг",
    "passwords": "пароль",
    "pii": "персональн",
    "incident_response": "инцидент",
    "social_engineering": "социальн",
}


def compute_profile(answers: list[dict]) -> dict[str, float]:
    """Return score 0..1 per topic. Missing topics default to 0.0."""
    totals: dict[str, int] = {t: 0 for t in TOPICS}
    corrects: dict[str, int] = {t: 0 for t in TOPICS}
    for a in answers:
        topic = a.get("topic", "")
        if topic in totals:
            totals[topic] += 1
            if a.get("is_correct"):
                corrects[topic] += 1
    return {t: (corrects[t] / totals[t] if totals[t] > 0 else 0.0) for t in TOPICS}


def select_topic(scores: dict[str, float], history: list[dict]) -> str:
    """Pick weakest-scoring topic; avoid last topic to prevent repetition."""
    last_topic = history[-1]["topic"] if history else None
    candidates = sorted(
        [t for t in TOPICS if t != last_topic], key=lambda t: scores.get(t, 0.0)
    )
    return candidates[0]


async def start_session(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Create a new diagnostic session and return the first question."""
    initial_scores = {t: 0.0 for t in TOPICS}
    first_topic = select_topic(initial_scores, history=[])

    question = await _generate_question(db, first_topic, recent_texts=[])

    session = DiagnosticSession(
        user_id=user_id,
        answers=[],
        question_count=1,
        is_finished=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info("diagnostic.start user_id=%s session_id=%s", user_id, session.id)
    return {
        "session_id": str(session.id),
        "question": _question_dict(question, first_topic),
    }


async def submit_answer(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    question_id: uuid.UUID,
    topic: str,
    selected_index: int,
) -> dict:
    """Score answer, update session, return next question or finish."""
    result = await db.execute(
        select(DiagnosticSession).where(DiagnosticSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None or session.user_id != user_id or session.is_finished:
        from app.core.exceptions import NotFoundException

        raise NotFoundException

    q_result = await db.execute(select(Question).where(Question.id == question_id))
    question = q_result.scalar_one_or_none()
    if question is None:
        from app.core.exceptions import NotFoundException

        raise NotFoundException

    # Bounds-check user-supplied selected_index before scoring (twin of vkr-g2h):
    # an out-of-range index is invalid input and must be rejected with 422, not
    # silently recorded as a wrong answer.
    if not 0 <= selected_index < len(question.options):
        from app.core.exceptions import ValidationException

        logger.warning(
            "diagnostic.index_out_of_range question_id=%s selected=%d options=%d",
            question_id,
            selected_index,
            len(question.options),
        )
        raise ValidationException

    is_correct = selected_index == question.correct_index

    new_answer = {
        "question_id": str(question_id),
        "topic": topic,
        "is_correct": is_correct,
    }
    updated_answers = session.answers + [new_answer]
    session.answers = updated_answers
    session.question_count += 1

    scores = compute_profile(updated_answers)
    finished = session.question_count >= MAX_QUESTIONS

    if finished:
        session.is_finished = True
        # Atomic completion (ФСТЭК-21): session.is_finished + the competency
        # profile/user-mark mutations + the diagnostic_completed audit row all
        # commit in ONE transaction owned here. finish_session(commit=False)
        # only flushes its mutations; this submit owns the single commit, so a
        # crash anywhere rolls the whole thing back — a completed diagnostic can
        # never persist without its audit row.
        profile = await finish_session(
            db, session_id=session.id, user_id=user_id, scores=scores, commit=False
        )
        await audit_service.write(
            db,
            user_id=user_id,
            action="diagnostic_completed",
            details={"session_id": str(session_id)},
            commit=False,
        )
        await db.commit()
        # Module auto-assignment is a best-effort side-effect AFTER the audited
        # "done" state is durable: assign_module owns its own commits and
        # per-module failures are swallowed, so it stays outside the atomic tx.
        weak_topics = [t for t, s in scores.items() if s < WEAK_THRESHOLD]
        if weak_topics:
            await _auto_assign_modules(db, user_id, weak_topics)
        logger.info("diagnostic.finish user_id=%s weak=%s", user_id, weak_topics)
        return {
            "is_correct": is_correct,
            "finished": True,
            "profile": profile,
            "question": None,
        }

    await db.commit()

    next_topic = select_topic(scores, history=updated_answers)
    recent_texts = [a.get("question_text", "") for a in updated_answers[-5:]]
    next_q = await _generate_question(db, next_topic, recent_texts=recent_texts)

    return {
        "is_correct": is_correct,
        "finished": False,
        "profile": None,
        "question": _question_dict(next_q, next_topic),
    }


async def finish_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    scores: dict[str, float] | None = None,
    *,
    commit: bool = True,
) -> dict[str, float]:
    """Compute final profile, upsert UserCompetencyProfile, auto-assign weak modules.

    commit=True (default, standalone callers): owns its own commit, then runs
    module auto-assignment — unchanged legacy behavior.

    commit=False (shared transaction): only stages the profile upsert + user
    mark; the CALLER owns the single commit (so they persist atomically with the
    diagnostic_completed audit row) and runs auto-assignment AFTER that commit.
    """
    if scores is None:
        result = await db.execute(
            select(DiagnosticSession).where(DiagnosticSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            return {}
        scores = compute_profile(session.answers)

    now = datetime.now(timezone.utc)

    # Upsert competency profiles
    existing = await db.execute(
        select(UserCompetencyProfile).where(UserCompetencyProfile.user_id == user_id)
    )
    profiles = {p.topic: p for p in existing.scalars().all()}

    for topic, score in scores.items():
        if topic in profiles:
            profiles[topic].score = score
            profiles[topic].updated_at = now
        else:
            db.add(
                UserCompetencyProfile(
                    user_id=user_id, topic=topic, score=score, updated_at=now
                )
            )

    # Mark user diagnostic as done
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.diagnostic_completed_at = now

    if not commit:
        # Stage our mutations into the shared transaction explicitly (don't rely
        # on the audit write's later flush); the caller owns the single commit +
        # post-commit auto-assignment (atomic with the diagnostic_completed row).
        await db.flush()
        return scores

    await db.commit()

    # Auto-assign modules for weak topics
    weak_topics = [t for t, s in scores.items() if s < WEAK_THRESHOLD]
    if weak_topics:
        await _auto_assign_modules(db, user_id, weak_topics)

    logger.info("diagnostic.finish user_id=%s weak=%s", user_id, weak_topics)
    return scores


async def _auto_assign_modules(
    db: AsyncSession, user_id: uuid.UUID, weak_topics: list[str]
) -> None:
    """Find published modules matching weak topics and assign them."""
    for topic in weak_topics:
        keyword = _TOPIC_MODULE_KEYWORDS.get(topic, topic)
        result = await db.execute(
            select(Module).where(
                Module.is_published.is_(True),
                Module.title.ilike(f"%{keyword}%"),
            )
        )
        modules = result.scalars().all()
        for module in modules:
            try:
                await learning_service.assign_module(
                    db, user_id=user_id, module_id=module.id
                )
            except Exception as exc:
                logger.warning(
                    "diagnostic.assign_failed topic=%s module=%s error=%s",
                    topic,
                    module.id,
                    exc,
                )


async def _generate_question(
    db: AsyncSession, topic: str, recent_texts: list[str]
) -> Question:
    """Generate a question on the given topic using the LLM."""
    content = _TOPIC_CONTENT.get(topic, topic)
    schema = await llm_service.generate_question(
        module_title=f"Диагностика: {topic}",
        module_content=content,
        recent_questions=recent_texts,
    )
    question = Question(
        module_id=None,  # diagnostic questions have no module
        text=schema.text,
        options=schema.options,
        correct_index=schema.correct_index,
        explanation=schema.explanation,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


def _question_dict(question: Question, topic: str) -> dict:
    return {
        "id": str(question.id),
        "topic": topic,
        "text": question.text,
        "options": question.options,
    }
