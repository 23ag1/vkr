import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.user import User

logger = logging.getLogger(__name__)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("auth.login_failed reason=user_not_found email=%s", email)
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning("auth.login_failed reason=wrong_password email=%s user_id=%s", email, user.id)
        return None
    logger.info("auth.login_ok email=%s user_id=%s role=%s", email, user.id, user.role)
    return user


def build_token_pair(user: User) -> dict:
    payload = {"sub": str(user.id), "role": user.role}
    logger.info("auth.token_issued user_id=%s role=%s", user.id, user.role)
    return {
        "access_token": create_access_token({**payload, "token_type": "access"}),
        "refresh_token": create_refresh_token({**payload, "token_type": "refresh"}),
    }
