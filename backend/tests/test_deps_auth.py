import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from tests.conftest import BASE_ENV


def _make_user(role: str = "employee", is_active: bool = True):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = is_active
    return u


def _make_token(user_id: str, role: str = "employee") -> str:
    from unittest.mock import patch as _patch
    import app.core.security as sec
    with _patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        reload(sec)
        return sec.create_access_token({"sub": user_id, "role": role, "token_type": "access"})


@pytest.mark.anyio
async def test_get_current_user_valid_token():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.deps as deps_module
        reload(deps_module)

        user = _make_user()
        token = _make_token(str(user.id))

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db = AsyncMock()
        db.execute.return_value = mock_result

        creds = HTTPAuthorizationCredentials(scheme="bearer", credentials=token)
        result = await deps_module.get_current_user(credentials=creds, db=db)
        assert result is user


@pytest.mark.anyio
async def test_get_current_user_no_credentials_raises_401():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.deps as deps_module
        reload(deps_module)

        db = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await deps_module.get_current_user(credentials=None, db=db)
        assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_invalid_token_raises_401():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.deps as deps_module
        reload(deps_module)

        db = AsyncMock()
        creds = HTTPAuthorizationCredentials(scheme="bearer", credentials="bad.token.here")
        with pytest.raises(HTTPException) as exc:
            await deps_module.get_current_user(credentials=creds, db=db)
        assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_inactive_user_raises_401():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.deps as deps_module
        reload(deps_module)

        user = _make_user(is_active=False)
        token = _make_token(str(user.id))

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db = AsyncMock()
        db.execute.return_value = mock_result

        creds = HTTPAuthorizationCredentials(scheme="bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            await deps_module.get_current_user(credentials=creds, db=db)
        assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_require_role_allows_correct_role():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.deps as deps_module
        reload(deps_module)

        user = _make_user(role="admin")
        checker = deps_module.require_role("admin")
        result = await checker(current_user=user)
        assert result is user


@pytest.mark.anyio
async def test_require_role_rejects_wrong_role():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.deps as deps_module
        reload(deps_module)

        user = _make_user(role="employee")
        checker = deps_module.require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await checker(current_user=user)
        assert exc.value.status_code == 403
