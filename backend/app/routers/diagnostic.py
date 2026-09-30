import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.diagnostic as diagnostic_service
from app.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, ok

router = APIRouter()

_employee = Depends(require_role("employee"))


class AnswerBody(BaseModel):
    session_id: uuid.UUID
    question_id: uuid.UUID
    topic: str
    selected_index: int


@router.post("/start", response_model=ApiResponse[dict])
async def start_diagnostic(
    current_user: User = Depends(require_role("employee")),
    db: AsyncSession = Depends(get_db),
):
    result = await diagnostic_service.start_session(db, user_id=current_user.id)
    return ok(result)


@router.post("/answer", response_model=ApiResponse[dict])
async def submit_answer(
    body: AnswerBody,
    current_user: User = Depends(require_role("employee")),
    db: AsyncSession = Depends(get_db),
):
    result = await diagnostic_service.submit_answer(
        db,
        session_id=body.session_id,
        user_id=current_user.id,
        question_id=body.question_id,
        topic=body.topic,
        selected_index=body.selected_index,
    )
    return ok(result)
