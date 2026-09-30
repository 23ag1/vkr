import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
from app.core.exceptions import NotFoundException, ValidationException
import app.services.llm as llm_service
import app.services.module as module_service
from app.models.test import Question, UserAnswer

logger = logging.getLogger(__name__)


async def _recent_question_texts(
    db: AsyncSession, module_id: uuid.UUID, limit: int = 8
) -> list[str]:
    result = await db.execute(
        select(Question.text)
        .where(Question.module_id == module_id)
        .order_by(Question.created_at.desc())
        .limit(limit)
    )
    return [row[0] for row in result.fetchall()]


async def generate_and_persist_question(
    db: AsyncSession, module_id: uuid.UUID
) -> Question:
    module = await module_service.get_module(db, module_id)
    recent = await _recent_question_texts(db, module_id)
    logger.info(
        "testing.generate_start module_id=%s recent_count=%d", module_id, len(recent)
    )

    schema = await llm_service.generate_question(
        module.title, module.content_md, recent_questions=recent
    )

    question = Question(
        module_id=module.id,
        text=schema.text,
        options=schema.options,
        correct_index=schema.correct_index,
        explanation=schema.explanation,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    logger.info(
        "testing.generate_ok question_id=%s module_id=%s", question.id, module_id
    )
    return question


async def submit_answer(
    db: AsyncSession,
    user_id: uuid.UUID,
    question_id: uuid.UUID,
    selected_index: int,
) -> dict:
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if question is None:
        logger.warning("testing.question_not_found id=%s", question_id)
        raise NotFoundException

    if not 0 <= selected_index < len(question.options):
        logger.warning(
            "testing.index_out_of_range question_id=%s selected=%d options=%d",
            question_id,
            selected_index,
            len(question.options),
        )
        raise ValidationException

    is_correct = selected_index == question.correct_index
    logger.info(
        "testing.answer user_id=%s question_id=%s selected=%d correct=%d is_correct=%s",
        user_id,
        question_id,
        selected_index,
        question.correct_index,
        is_correct,
    )

    explanation = question.explanation
    if not is_correct:
        try:
            explanation = await llm_service.generate_explanation(
                question_text=question.text,
                correct_answer=question.options[question.correct_index],
                user_answer=question.options[selected_index],
                context_chunks=[],
            )
            logger.info("testing.explanation_generated question_id=%s", question_id)
        except Exception as exc:
            logger.warning(
                "testing.explanation_failed question_id=%s error=%s", question_id, exc
            )

    answer = UserAnswer(
        user_id=user_id,
        question_id=question_id,
        selected_index=selected_index,
        is_correct=is_correct,
    )
    db.add(answer)
    # Audit row shares the answer's transaction: a single atomic commit so the
    # recorded answer and its audit entry persist together (no crash-gap).
    await audit_service.write(
        db,
        user_id=user_id,
        action="test_answer_submitted",
        details={
            "question_id": str(question_id),
            "is_correct": is_correct,
            "module_id": str(question.module_id),
        },
        commit=False,
    )
    await db.commit()

    return {
        "is_correct": is_correct,
        "explanation": explanation,
        "correct_index": question.correct_index,
    }


async def get_history(db: AsyncSession, user_id: uuid.UUID) -> list[UserAnswer]:
    result = await db.execute(
        select(UserAnswer)
        .where(UserAnswer.user_id == user_id)
        .order_by(UserAnswer.created_at.desc())
    )
    history = result.scalars().all()
    logger.info("testing.history user_id=%s count=%d", user_id, len(history))
    return history
