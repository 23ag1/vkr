import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_user(role="admin"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = True
    return u


def _setup_app(role="admin"):
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
    return main_module.app


@pytest.mark.anyio
async def test_analytics_overview_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.analytics as svc
        app_inst = _setup_app("admin")
        overview = {"total_users": 10, "completion_rate": 0.75, "avg_score": 82.0,
                    "phishing_click_rate": 0.20}
        with patch.object(svc, "get_overview", AsyncMock(return_value=overview)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/analytics/overview")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_analytics_overview_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.get("/api/analytics/overview")
        assert resp.status_code == 403
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_analytics_user_profile_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.analytics as svc
        app_inst = _setup_app("admin")
        profile = {"user_id": str(uuid.uuid4()), "modules_completed": 3,
                   "avg_score": 85.0, "phishing_clicks": 1}
        uid = uuid.uuid4()
        with patch.object(svc, "get_user_profile", AsyncMock(return_value=profile)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/analytics/users/{uid}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()
