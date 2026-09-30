"""Tests for TOTP MFA service (vkr-pno)."""
import importlib
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BASE_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
    "SECRET_KEY": "testsecret",
    "OPENAI_API_KEY": "sk-test",
}


def _make_db(rows=None):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = rows
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _load_mfa():
    with patch.dict("os.environ", BASE_ENV):
        if "app.services.mfa" in sys.modules:
            return importlib.reload(sys.modules["app.services.mfa"])
        import app.services.mfa as m
        return m


class FakeUser:
    def __init__(self, role="admin", mfa_enabled=False, totp_secret=None):
        import uuid
        self.id = uuid.uuid4()
        self.email = "admin@example.com"
        self.role = role
        self.mfa_enabled = mfa_enabled
        self.totp_secret = totp_secret


@pytest.mark.asyncio
async def test_setup_mfa_returns_secret_and_uri():
    mfa = _load_mfa()
    user = FakeUser(role="admin")
    db = _make_db(rows=user)

    result = await mfa.setup_mfa(db, user)

    assert "secret" in result
    assert "otpauth_uri" in result
    assert len(result["secret"]) > 10
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_mfa_correct_code_enables():
    mfa = _load_mfa()
    import pyotp
    secret = pyotp.random_base32()
    user = FakeUser(role="admin", totp_secret=secret)
    db = _make_db(rows=user)

    code = pyotp.TOTP(secret).now()
    result = await mfa.verify_and_enable_mfa(db, user, code)

    assert result is True
    assert user.mfa_enabled is True
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_mfa_wrong_code_returns_false():
    mfa = _load_mfa()
    import pyotp
    secret = pyotp.random_base32()
    user = FakeUser(role="admin", totp_secret=secret)
    db = _make_db(rows=user)

    result = await mfa.verify_and_enable_mfa(db, user, "000000")

    assert result is False
    assert user.mfa_enabled is False
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_totp_valid():
    mfa = _load_mfa()
    import pyotp
    secret = pyotp.random_base32()
    user = FakeUser(role="admin", mfa_enabled=True, totp_secret=secret)

    code = pyotp.TOTP(secret).now()
    assert mfa.check_totp(user, code) is True


@pytest.mark.asyncio
async def test_check_totp_invalid():
    mfa = _load_mfa()
    import pyotp
    secret = pyotp.random_base32()
    user = FakeUser(role="admin", mfa_enabled=True, totp_secret=secret)

    assert mfa.check_totp(user, "000000") is False
