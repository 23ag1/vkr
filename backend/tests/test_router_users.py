import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_user_orm(role="admin"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "admin@test.com"
    u.full_name = "Admin"
    u.role = role
    u.is_active = True
    u.department_id = None
    return u


def _setup_app(current_user):
    from importlib import reload
    import app.main as main_module
    reload(main_module)
    from app import deps

    async def fake_db():
        yield AsyncMock()

    async def fake_current_user():
        return current_user

    main_module.app.dependency_overrides[deps.get_db] = fake_db
    main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user
    return main_module.app


@pytest.mark.anyio
async def test_list_users_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.user as user_svc
        admin = _make_user_orm("admin")
        app_inst = _setup_app(admin)

        target_users = [_make_user_orm(), _make_user_orm()]
        with patch.object(user_svc, "list_users", AsyncMock(return_value=(target_users, 2))):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/users")

        assert resp.status_code == 200
        from app.main import app
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_users_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        employee = _make_user_orm("employee")
        app_inst = _setup_app(employee)

        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
            resp = await ac.get("/api/users")

        assert resp.status_code == 403
        from app.main import app
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_user_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.user as user_svc
        admin = _make_user_orm("admin")
        app_inst = _setup_app(admin)

        new_user = _make_user_orm()
        with patch.object(user_svc, "create_user", AsyncMock(return_value=new_user)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/api/users", json={
                    "email": "new@test.com", "password": "password123",
                    "full_name": "New User", "role": "employee"
                })

        assert resp.status_code == 201
        from app.main import app
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_user_by_id_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.user as user_svc
        admin = _make_user_orm("admin")
        app_inst = _setup_app(admin)

        target = _make_user_orm()
        with patch.object(user_svc, "get_user", AsyncMock(return_value=target)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/users/{target.id}")

        assert resp.status_code == 200
        from app.main import app
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_get_user_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.user as user_svc
        from fastapi import HTTPException
        admin = _make_user_orm("admin")
        app_inst = _setup_app(admin)

        with patch.object(user_svc, "get_user",
                          AsyncMock(side_effect=HTTPException(status_code=404, detail="not found"))):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/users/{uuid.uuid4()}")

        assert resp.status_code == 404
        from app.main import app
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_deactivate_user_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.user as user_svc
        admin = _make_user_orm("admin")
        app_inst = _setup_app(admin)

        target = _make_user_orm()
        target.is_active = False
        with patch.object(user_svc, "deactivate_user", AsyncMock(return_value=target)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.delete(f"/api/users/{target.id}")

        assert resp.status_code == 200
        from app.main import app
        app.dependency_overrides.clear()
