import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


async def list_users(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> tuple[list[User], int]:
    total_result = await db.execute(select(func.count()).select_from(User))
    total = total_result.scalar_one()
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    logger.info("user.list count=%d skip=%d limit=%d", len(users), skip, limit)
    return users, total


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("user.not_found id=%s", user_id)
        raise NotFoundException
    return user


async def create_user(
    db: AsyncSession, data: UserCreate, *, commit: bool = True
) -> User:
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        department_id=data.department_id,
    )
    db.add(user)
    if commit:
        await db.commit()
    else:
        # Caller owns the commit so this insert and its audit row are atomic.
        await db.flush()
    await db.refresh(user)
    logger.info("user.create id=%s email=%s role=%s", user.id, user.email, user.role)
    return user


async def update_user(db: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = await get_user(db, user_id)
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(user, field, value)
    await db.commit()
    logger.info("user.update id=%s fields=%s", user_id, list(fields.keys()))
    return user


async def deactivate_user(
    db: AsyncSession, user_id: uuid.UUID, *, commit: bool = True
) -> User:
    user = await get_user(db, user_id)
    user.is_active = False
    if commit:
        await db.commit()
    else:
        # Caller owns the commit so this update and its audit row are atomic.
        await db.flush()
    logger.info("user.deactivate id=%s", user_id)
    return user
