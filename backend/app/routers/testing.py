from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.testing as testing_service
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ok
from app.schemas.testing import (
    AnswerFeedback,
    AnswerHistoryItem,
    AnswerRequest,
    GenerateRequest,
    QuestionResponse,
)

router = APIRouter()


@router.post("/generate", response_model=ApiResponse[QuestionResponse])
async def generate_question(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await testing_service.generate_and_persist_question(db, body.module_id)
    return ok(QuestionResponse.model_validate(question))


@router.post("/answer", response_model=ApiResponse[AnswerFeedback])
async def submit_answer(
    body: AnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback = await testing_service.submit_answer(
        db, current_user.id, body.question_id, body.selected_index
    )
    return ok(AnswerFeedback(**feedback))


@router.get("/history", response_model=ApiResponse[list[AnswerHistoryItem]])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history = await testing_service.get_history(db, current_user.id)
    return ok([AnswerHistoryItem.model_validate(a) for a in history])
