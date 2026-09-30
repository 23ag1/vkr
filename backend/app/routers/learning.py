import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.learning as learning_service
from app.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, ok
from app.schemas.learning import AssignRequest, ProgressResponse, ProgressUpdate

router = APIRouter()

_admin = Depends(require_role("admin"))


@router.get("/my", response_model=ApiResponse[list[ProgressResponse]])
async def get_my_path(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await learning_service.get_my_path(db, current_user.id)
    return ok([ProgressResponse.model_validate(p) for p in items])


@router.post("/assign", response_model=ApiResponse[ProgressResponse],
             status_code=status.HTTP_201_CREATED, dependencies=[_admin])
async def assign_module(body: AssignRequest, db: AsyncSession = Depends(get_db)):
    progress = await learning_service.assign_module(db, body.user_id, body.module_id)
    return ok(ProgressResponse.model_validate(progress))


@router.patch("/{progress_id}/progress", response_model=ApiResponse[ProgressResponse])
async def update_progress(
    progress_id: uuid.UUID,
    body: ProgressUpdate,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    progress = await learning_service.update_progress(db, progress_id, body)
    return ok(ProgressResponse.model_validate(progress))
