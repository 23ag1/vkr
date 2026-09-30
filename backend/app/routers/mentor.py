import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.mentor as mentor_service
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse, ok
from app.schemas.mentor import MessageCreate, MessageResponse, SessionCreate, SessionResponse

router = APIRouter()


@router.get("/sessions", response_model=ApiResponse[list[SessionResponse]])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await mentor_service.list_sessions(db, current_user.id)
    return ok([SessionResponse.model_validate(s) for s in sessions])


@router.post("/sessions", response_model=ApiResponse[SessionResponse],
             status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await mentor_service.create_session(
        db, current_user.id, title=body.title, module_id=body.module_id
    )
    return ok(SessionResponse.model_validate(session))


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse[list[MessageResponse]])
async def list_messages(
    session_id: uuid.UUID,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await mentor_service.list_messages(db, session_id)
    return ok([MessageResponse.model_validate(m) for m in messages])


@router.post("/sessions/{session_id}/messages", response_model=ApiResponse[MessageResponse],
             status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: uuid.UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reply = await mentor_service.send_message(db, session_id, current_user.id, body.content)
    return ok(MessageResponse.model_validate(reply))
