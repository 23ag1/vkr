import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_user_orm(role="employee"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "a@b.com"
    u.full_name = "Alice"
    u.role = role
    u.is_active = True
    u.hashed_password = "hashed"
    u.department_id = None
    return u


@pytest.mark.anyio
async def test_list_users_returns_list():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)

        users = [_make_user_orm(), _make_user_orm()]
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = users
        db = _mock_db()
        db.execute.side_effect = [count_result, list_result]

        result, total = await svc.list_users(db, skip=0, limit=20)
        assert result == users
        assert total == 2


@pytest.mark.anyio
async def test_get_user_returns_user():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)

        user = _make_user_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.get_user(db, user.id)
        assert result is user


@pytest.mark.anyio
async def test_get_user_not_found_raises_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.get_user(db, uuid.uuid4())
        assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_create_user_hashes_password():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)
        from app.schemas.user import UserCreate

        data = UserCreate(
            email="new@test.com",
            password="password123",
            full_name="New",
            role="employee",
        )
        db = _mock_db()
        db.refresh = AsyncMock(side_effect=lambda u: None)

        await svc.create_user(db, data)
        db.add.assert_called_once()
        added_user = db.add.call_args[0][0]
        assert added_user.hashed_password != "password123"
        assert added_user.hashed_password.startswith("$2")


@pytest.mark.anyio
async def test_update_user_applies_changes():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)
        from app.schemas.user import UserUpdate

        user = _make_user_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db = _mock_db()
        db.execute.return_value = mock_result

        data = UserUpdate(full_name="Updated Name")
        await svc.update_user(db, user.id, data)
        assert user.full_name == "Updated Name"


@pytest.mark.anyio
async def test_deactivate_user_sets_inactive():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)

        user = _make_user_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.deactivate_user(db, user.id)
        assert user.is_active is False


@pytest.mark.anyio
async def test_create_user_commit_false_flushes_not_commits():
    """commit=False keeps the insert in the caller's transaction so the router
    can commit it atomically with the audit row."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)
        from app.schemas.user import UserCreate

        data = UserCreate(
            email="new@test.com",
            password="password123",
            full_name="New",
            role="employee",
        )
        db = _mock_db()

        await svc.create_user(db, data, commit=False)
        assert db.flush.await_count == 1
        assert db.commit.await_count == 0


@pytest.mark.anyio
async def test_deactivate_user_commit_false_flushes_not_commits():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.user as svc

        reload(svc)

        user = _make_user_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.deactivate_user(db, user.id, commit=False)
        assert db.flush.await_count == 1
        assert db.commit.await_count == 0
