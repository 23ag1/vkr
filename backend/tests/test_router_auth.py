import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV

# ── helpers ────────────────────────────────────────────────────────────────

def _make_user_orm():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "admin@test.com"
    u.full_name = "Admin"
    u.role = "admin"
    u.is_active = True
    u.mfa_enabled = False
    u.department_id = None
    return u


def _token_for(user) -> str:
    from app.services.auth import build_token_pair
    return build_token_pair(user)["access_token"]


def _make_app(auth_svc_mock):
    from importlib import reload
    import app.main as main_module
    reload(main_module)
    from app import deps

    # override get_db so no real DB needed
    async def fake_db():
        yield AsyncMock()

    main_module.app.dependency_overrides[deps.get_db] = fake_db

    # patch the auth service used by the router
    import app.routers.auth as auth_router_module
    auth_router_module.auth_service = auth_svc_mock

    return main_module.app


# ── tests ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_login_success():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.routers.auth as router_module
        reload(router_module)
        import app.main as main_module
        reload(main_module)

        user = _make_user_orm()
        mock_svc = MagicMock()
        mock_svc.authenticate_user = AsyncMock(return_value=user)
        mock_svc.build_token_pair = MagicMock(
            return_value={"access_token": "acc", "refresh_token": "ref"}
        )

        from app import deps
        async def fake_db():
            yield AsyncMock()

        main_module.app.dependency_overrides[deps.get_db] = fake_db
        router_module._auth_service = mock_svc

        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/api/auth/login", json={"email": "admin@test.com", "password": "pass"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["access_token"] == "acc"
        assert body["error"] is None

        main_module.app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_login_wrong_credentials():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.routers.auth as router_module
        reload(router_module)
        import app.main as main_module
        reload(main_module)

        mock_svc = MagicMock()
        mock_svc.authenticate_user = AsyncMock(return_value=None)

        from app import deps
        async def fake_db():
            yield AsyncMock()

        main_module.app.dependency_overrides[deps.get_db] = fake_db
        router_module._auth_service = mock_svc

        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.post("/api/auth/login", json={"email": "x@x.com", "password": "wrong"})

        assert resp.status_code == 401
        main_module.app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_me_requires_auth():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.main as main_module
        reload(main_module)

        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/auth/me")

        assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_returns_profile():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.main as main_module
        reload(main_module)

        user = _make_user_orm()
        from app import deps

        async def fake_current_user():
            return user

        main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user

        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/auth/me")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["email"] == user.email
        main_module.app.dependency_overrides.clear()
