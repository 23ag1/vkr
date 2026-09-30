import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
from app.core.exceptions import NotFoundException
from app.models.learning import UserModuleProgress
from app.schemas.common import ProgressStatus
from app.schemas.learning import ProgressUpdate

logger = logging.getLogger(__name__)


async def get_my_path(db: AsyncSession, user_id: uuid.UUID) -> list[UserModuleProgress]:
    result = await db.execute(
        select(UserModuleProgress).where(UserModuleProgress.user_id == user_id)
    )
    path = result.scalars().all()
    logger.info("learning.get_path user_id=%s count=%d", user_id, len(path))
    return path


async def assign_module(
    db: AsyncSession, user_id: uuid.UUID, module_id: uuid.UUID
) -> UserModuleProgress:
    progress = UserModuleProgress(
        user_id=user_id,
        module_id=module_id,
        status=ProgressStatus.NOT_STARTED,
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    logger.info(
        "learning.assign user_id=%s module_id=%s progress_id=%s",
        user_id,
        module_id,
        progress.id,
    )
    return progress


async def update_progress(
    db: AsyncSession, progress_id: uuid.UUID, data: ProgressUpdate
) -> UserModuleProgress:
    result = await db.execute(
        select(UserModuleProgress).where(UserModuleProgress.id == progress_id)
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        logger.warning("learning.progress_not_found id=%s", progress_id)
        raise NotFoundException

    prev_status = progress.status
    progress.status = data.status
    if data.score is not None:
        progress.score = data.score
    if data.status == ProgressStatus.COMPLETED and progress.completed_at is None:
        progress.completed_at = datetime.now(timezone.utc)

    if (
        data.status == ProgressStatus.COMPLETED
        and prev_status != ProgressStatus.COMPLETED
    ):
        # Audit shares the progress transaction: a completion and its audit row
        # commit atomically (a completed module always leaves an audit trail).
        await audit_service.write(
            db,
            user_id=progress.user_id,
            action="module_completed",
            details={"module_id": str(progress.module_id), "score": data.score},
            commit=False,
        )
    await db.commit()
    logger.info(
        "learning.progress_update id=%s user_id=%s module_id=%s status=%s->%s score=%s",
        progress_id,
        progress.user_id,
        progress.module_id,
        prev_status,
        data.status,
        data.score,
    )
    return progress
