import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_dept_orm():
    d = MagicMock()
    d.id = uuid.uuid4()
    d.name = "Engineering"
    d.parent_id = None
    return d


def _make_admin():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = "admin"
    u.is_active = True
    return u


def _setup_app():
    from importlib import reload
    import app.main as main_module
    reload(main_module)
    from app import deps

    admin = _make_admin()

    async def fake_db():
        yield AsyncMock()

    async def fake_current_user():
        return admin

    main_module.app.dependency_overrides[deps.get_db] = fake_db
    main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user
    return main_module.app


@pytest.mark.anyio
async def test_list_departments_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.department as svc
        app_inst = _setup_app()
        depts = [_make_dept_orm()]
        with patch.object(svc, "list_departments", AsyncMock(return_value=depts)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/departments")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_department_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.department as svc
        app_inst = _setup_app()
        dept = _make_dept_orm()
        with patch.object(svc, "create_department", AsyncMock(return_value=dept)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/api/departments", json={"name": "Finance"})
        assert resp.status_code == 201
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_department_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.department as svc
        app_inst = _setup_app()
        dept = _make_dept_orm()
        with patch.object(svc, "get_department", AsyncMock(return_value=dept)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/departments/{dept.id}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_department_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.department as svc
        from fastapi import HTTPException
        app_inst = _setup_app()
        with patch.object(svc, "get_department",
                          AsyncMock(side_effect=HTTPException(status_code=404, detail="not found"))):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/departments/{uuid.uuid4()}")
        assert resp.status_code == 404
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_department_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.department as svc
        app_inst = _setup_app()
        dept = _make_dept_orm()
        with patch.object(svc, "update_department", AsyncMock(return_value=dept)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.put(f"/api/departments/{dept.id}", json={"name": "Updated"})
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_department_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.department as svc
        app_inst = _setup_app()
        dept = _make_dept_orm()
        with patch.object(svc, "delete_department", AsyncMock(return_value=None)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.delete(f"/api/departments/{dept.id}")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()
