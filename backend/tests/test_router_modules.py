import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_module_orm(published=True):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.title = "Phishing Basics"
    m.description = "Learn phishing"
    m.content_md = "# Content"
    m.target_roles = ["employee"]
    m.order_index = 0
    m.is_published = published
    m.briefing_type = "none"
    return m


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
async def test_list_modules_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        app_inst = _setup_app("employee")
        modules = [_make_module_orm()]
        with patch.object(svc, "list_modules", AsyncMock(return_value=modules)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/modules")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_module_admin_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        app_inst = _setup_app("admin")
        module = _make_module_orm(False)
        with patch.object(svc, "create_module", AsyncMock(return_value=module)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/api/modules", json={
                    "title": "Test", "description": "Desc",
                    "content_md": "# H", "target_roles": ["employee"], "order_index": 0
                })
        assert resp.status_code == 201
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_module_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.post("/api/modules", json={
                "title": "Test", "description": "Desc",
                "content_md": "# H", "target_roles": ["employee"], "order_index": 0
            })
        assert resp.status_code == 403
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_module_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        app_inst = _setup_app("employee")
        module = _make_module_orm()
        with patch.object(svc, "get_module", AsyncMock(return_value=module)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/modules/{module.id}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_module_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        from fastapi import HTTPException
        app_inst = _setup_app("employee")
        with patch.object(svc, "get_module",
                          AsyncMock(side_effect=HTTPException(status_code=404, detail="not found"))):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/modules/{uuid.uuid4()}")
        assert resp.status_code == 404
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_module_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        app_inst = _setup_app("admin")
        module = _make_module_orm()
        with patch.object(svc, "update_module", AsyncMock(return_value=module)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.put(f"/api/modules/{module.id}", json={"title": "Updated"})
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_publish_module_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        app_inst = _setup_app("admin")
        module = _make_module_orm(True)
        with patch.object(svc, "publish_module", AsyncMock(return_value=module)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post(f"/api/modules/{module.id}/publish")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_module_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.module as svc
        app_inst = _setup_app("admin")
        with patch.object(svc, "delete_module", AsyncMock(return_value=None)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.delete(f"/api/modules/{uuid.uuid4()}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()
