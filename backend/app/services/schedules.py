import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.learning as learning_service
from app.core.exceptions import NotFoundException
from app.models.learning import UserModuleProgress
from app.models.schedule import TrainingSchedule
from app.models.user import User
from app.schemas.schedules import ScheduleCreate

logger = logging.getLogger(__name__)


async def list_schedules(db: AsyncSession) -> list[TrainingSchedule]:
    result = await db.execute(
        select(TrainingSchedule).order_by(TrainingSchedule.created_at.desc())
    )
    return result.scalars().all()


async def create_schedule(db: AsyncSession, data: ScheduleCreate) -> TrainingSchedule:
    schedule = TrainingSchedule(
        action=data.action,
        cadence=data.cadence,
        module_id=data.module_id,
        target_roles=data.target_roles,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    logger.info(
        "schedule.create id=%s action=%s cadence=%s",
        schedule.id,
        schedule.action,
        schedule.cadence,
    )
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> None:
    result = await db.execute(
        select(TrainingSchedule).where(TrainingSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise NotFoundException
    await db.delete(schedule)
    await db.commit()
    logger.info("schedule.delete id=%s", schedule_id)


async def trigger_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(TrainingSchedule).where(TrainingSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise NotFoundException

    assigned = 0

    if schedule.action == "assign_module" and schedule.module_id:
        users_query = select(User).where(User.is_active.is_(True))
        if schedule.target_roles:
            users_query = users_query.where(User.role.in_(schedule.target_roles))
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()

        for user in users:
            existing = await db.execute(
                select(UserModuleProgress)
                .where(UserModuleProgress.user_id == user.id)
                .where(UserModuleProgress.module_id == schedule.module_id)
            )
            if existing.scalar_one_or_none() is None:
                await learning_service.assign_module(db, user.id, schedule.module_id)
                assigned += 1

    schedule.last_triggered_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info(
        "schedule.trigger id=%s action=%s assigned=%d",
        schedule_id,
        schedule.action,
        assigned,
    )
    return {
        "schedule_id": str(schedule_id),
        "action": schedule.action,
        "assigned": assigned,
    }
