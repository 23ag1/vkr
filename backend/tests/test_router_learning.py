import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_progress_orm(status="not_started"):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.user_id = uuid.uuid4()
    p.module_id = uuid.uuid4()
    p.status = status
    p.score = None
    p.completed_at = None
    return p


def _make_user(role="employee"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = True
    return u


def _setup_app(role="employee"):
    from importlib import reload
    import app.main as main_module
    reload(main_module)
    from app import deps

    user = _make_user(role)

    async def fake_db():
        yield AsyncMock()

    async def fake_current_user():
        return user

    main_module.app.dependency_overrides[deps.get_db] = fake_db
    main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user
    return main_module.app, user


@pytest.mark.anyio
async def test_get_my_path_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.learning as svc
        app_inst, _ = _setup_app("employee")
        items = [_make_progress_orm("in_progress")]
        with patch.object(svc, "get_my_path", AsyncMock(return_value=items)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/learning/my")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_assign_module_admin_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.learning as svc
        app_inst, _ = _setup_app("admin")
        progress = _make_progress_orm()
        with patch.object(svc, "assign_module", AsyncMock(return_value=progress)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/api/learning/assign", json={
                    "user_id": str(uuid.uuid4()),
                    "module_id": str(uuid.uuid4()),
                })
        assert resp.status_code == 201
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_assign_module_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst, _ = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.post("/api/learning/assign", json={
                "user_id": str(uuid.uuid4()),
                "module_id": str(uuid.uuid4()),
            })
        assert resp.status_code == 403
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_progress_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.learning as svc
        app_inst, _ = _setup_app("employee")
        progress = _make_progress_orm("in_progress")
        with patch.object(svc, "update_progress", AsyncMock(return_value=progress)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.patch(f"/api/learning/{progress.id}/progress",
                                      json={"status": "in_progress"})
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()
