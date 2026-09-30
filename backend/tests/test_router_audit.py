import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_user(role="admin"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = True
    return u


def _make_log_orm(action="login"):
    log = MagicMock()
    log.id = uuid.uuid4()
    log.user_id = uuid.uuid4()
    log.action = action
    log.details = {"x": 1}
    log.ip_address = "127.0.0.1"
    log.created_at = datetime.now(timezone.utc)
    return log


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
async def test_list_audit_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.audit as svc
        app_inst = _setup_app("admin")
        with patch.object(svc, "list_logs", AsyncMock(return_value=[_make_log_orm("login")])):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/audit")
        assert resp.status_code == 200
        body = resp.json()
        assert body["error"] is None
        assert len(body["data"]) == 1
        assert body["data"][0]["action"] == "login"
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_audit_security_specialist_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.audit as svc
        app_inst = _setup_app("security_specialist")
        with patch.object(svc, "list_logs", AsyncMock(return_value=[])):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/audit")
        assert resp.status_code == 200
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_audit_employee_forbidden():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.get("/api/audit")
        assert resp.status_code == 403
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_audit_manager_forbidden():
    """manager role does not have access to raw audit log (only aggregated analytics)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("manager")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.get("/api/audit")
        assert resp.status_code == 403
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_export_audit_csv():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.audit as svc
        app_inst = _setup_app("admin")
        with patch.object(svc, "export_csv", AsyncMock(return_value="id,user_id,action\n1,2,login\n")):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/audit/export?format=csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "login" in resp.text
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_export_audit_forbidden_for_employee():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.get("/api/audit/export?format=csv")
        assert resp.status_code == 403
        app_inst.dependency_overrides.clear()
