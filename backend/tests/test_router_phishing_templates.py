import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_template_orm():
    t = MagicMock()
    t.id = uuid.uuid4()
    t.name = "IT Alert"
    t.subject = "Urgent: action required"
    t.body_html = "<p>Click here</p>"
    t.difficulty = "medium"
    return t


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
async def test_list_templates_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_templates as svc
        app_inst = _setup_app("admin")
        with patch.object(svc, "list_templates", AsyncMock(return_value=[_make_template_orm()])):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/phishing/templates")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_templates_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.get("/api/phishing/templates")
        assert resp.status_code == 403
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_template_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_templates as svc
        app_inst = _setup_app("admin")
        t = _make_template_orm()
        with patch.object(svc, "create_template", AsyncMock(return_value=t)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/api/phishing/templates", json={
                    "name": "IT Alert", "subject": "Urgent",
                    "body_html": "<p>Click</p>", "difficulty": "medium"
                })
        assert resp.status_code == 201
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_template_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_templates as svc
        app_inst = _setup_app("admin")
        t = _make_template_orm()
        with patch.object(svc, "get_template", AsyncMock(return_value=t)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/phishing/templates/{t.id}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_template_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_templates as svc
        app_inst = _setup_app("admin")
        t = _make_template_orm()
        with patch.object(svc, "update_template", AsyncMock(return_value=t)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.put(f"/api/phishing/templates/{t.id}", json={"name": "Updated"})
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_template_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_templates as svc
        app_inst = _setup_app("admin")
        with patch.object(svc, "delete_template", AsyncMock(return_value=None)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.delete(f"/api/phishing/templates/{uuid.uuid4()}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()
