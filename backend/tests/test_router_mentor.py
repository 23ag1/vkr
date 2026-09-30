import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_session_orm():
    s = MagicMock()
    s.id = uuid.uuid4()
    s.user_id = uuid.uuid4()
    s.module_id = None
    s.title = "New Chat"
    return s


def _make_message_orm(role="assistant"):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.session_id = uuid.uuid4()
    m.role = role
    m.content = "Hello!"
    m.sources = None
    return m


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
async def test_list_sessions_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.mentor as svc
        app_inst, _ = _setup_app()
        with patch.object(svc, "list_sessions", AsyncMock(return_value=[_make_session_orm()])):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/api/mentor/sessions")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_session_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.mentor as svc
        app_inst, _ = _setup_app()
        session = _make_session_orm()
        with patch.object(svc, "create_session", AsyncMock(return_value=session)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/api/mentor/sessions", json={"title": "My Chat"})
        assert resp.status_code == 201
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_messages_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.mentor as svc
        app_inst, _ = _setup_app()
        session = _make_session_orm()
        with patch.object(svc, "list_messages", AsyncMock(return_value=[_make_message_orm()])):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get(f"/api/mentor/sessions/{session.id}/messages")
        assert resp.status_code == 200
        from app.main import app; app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_send_message_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.mentor as svc
        app_inst, user = _setup_app()
        session = _make_session_orm()
        reply = _make_message_orm("assistant")
        with patch.object(svc, "send_message", AsyncMock(return_value=reply)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/mentor/sessions/{session.id}/messages",
                    json={"content": "What is phishing?"},
                )
        assert resp.status_code == 201
        from app.main import app; app.dependency_overrides.clear()
