import logging

import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)

APP_NAME = "VKR Security Training"


async def setup_mfa(db: AsyncSession, user: User) -> dict:
    secret = pyotp.random_base32()
    user.totp_secret = secret
    await db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=APP_NAME)
    logger.info("mfa.setup user_id=%s", user.id)
    return {"secret": secret, "otpauth_uri": uri}


async def verify_and_enable_mfa(db: AsyncSession, user: User, code: str) -> bool:
    if not user.totp_secret:
        return False
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code, valid_window=1):
        logger.warning("mfa.verify_fail user_id=%s", user.id)
        return False
    user.mfa_enabled = True
    await db.commit()
    logger.info("mfa.enabled user_id=%s", user.id)
    return True


def check_totp(user: User, code: str) -> bool:
    if not user.totp_secret:
        return False
    return pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)
