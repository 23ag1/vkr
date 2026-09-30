import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_user(password_plain: str = "secret123", is_active: bool = True):
    from app.core.security import hash_password
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "user@test.com"
    u.hashed_password = hash_password(password_plain)
    u.role = "employee"
    u.is_active = is_active
    u.full_name = "Test User"
    u.department_id = None
    return u


def _mock_db_with_user(user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = mock_result
    return db


@pytest.mark.anyio
async def test_authenticate_user_correct_password():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.auth as svc
        reload(svc)

        user = _make_user("password123")
        db = _mock_db_with_user(user)

        result = await svc.authenticate_user(db, "user@test.com", "password123")
        assert result is user


@pytest.mark.anyio
async def test_authenticate_user_wrong_password_returns_none():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.auth as svc
        reload(svc)

        user = _make_user("password123")
        db = _mock_db_with_user(user)

        result = await svc.authenticate_user(db, "user@test.com", "wrongpassword")
        assert result is None


@pytest.mark.anyio
async def test_authenticate_user_unknown_email_returns_none():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.auth as svc
        reload(svc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute.return_value = mock_result

        result = await svc.authenticate_user(db, "nobody@test.com", "pass")
        assert result is None


def test_build_token_pair_returns_both_tokens():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.auth as svc
        reload(svc)

        user = _make_user()
        tokens = svc.build_token_pair(user)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["access_token"] != tokens["refresh_token"]


def test_build_token_pair_access_token_decodable():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.auth as svc
        import app.core.security as sec
        reload(svc)
        reload(sec)

        user = _make_user()
        tokens = svc.build_token_pair(user)
        payload = sec.decode_token(tokens["access_token"])
        assert payload["sub"] == str(user.id)
        assert payload["role"] == user.role
        assert payload["token_type"] == "access"


def test_build_token_pair_refresh_token_has_correct_type():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.auth as svc
        import app.core.security as sec
        reload(svc)
        reload(sec)

        user = _make_user()
        tokens = svc.build_token_pair(user)
        payload = sec.decode_token(tokens["refresh_token"])
        assert payload["token_type"] == "refresh"
