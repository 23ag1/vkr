"""Tests for phishing tracking endpoints (vkr-9q3)."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_recipient(token="abc123token"):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.user_id = uuid.uuid4()
    r.campaign_id = uuid.uuid4()
    r.tracking_token = token
    r.opened_at = None
    r.clicked_at = None
    r.submitted_at = None
    r.reported_at = None
    return r


def _setup_app():
    from importlib import reload
    import app.main as main_module
    reload(main_module)
    from app import deps

    async def fake_db():
        yield AsyncMock()

    main_module.app.dependency_overrides[deps.get_db] = fake_db
    return main_module.app


@pytest.mark.anyio
async def test_track_open_returns_pixel():
    """GET /phishing/track/{token}/open returns 1x1 gif and sets opened_at."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        app_inst = _setup_app()
        recipient = _make_recipient()
        with patch.object(svc, "record_tracking_event", AsyncMock(return_value=recipient)) as mock_track:
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/phishing/track/abc123token/open")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "image/gif"
            mock_track.assert_awaited_once()
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_track_open_calls_opened_at_field():
    """open tracker must call record_tracking_event with 'opened_at' field."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        app_inst = _setup_app()
        recipient = _make_recipient()
        with patch.object(svc, "record_tracking_event", AsyncMock(return_value=recipient)) as mock_track:
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                await ac.get("/phishing/track/tok123/open")
        _, field = mock_track.call_args.args[1], mock_track.call_args.args[2]
        assert field == "opened_at"
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_track_submit_sets_submitted_at():
    """POST /phishing/track/{token}/submit records submitted_at, no credential storage."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        app_inst = _setup_app()
        recipient = _make_recipient()
        with patch.object(svc, "record_tracking_event", AsyncMock(return_value=recipient)) as mock_track:
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.post("/phishing/track/tok456/submit", json={"username": "u", "password": "p"})
        assert resp.status_code == 200
        _, field = mock_track.call_args.args[1], mock_track.call_args.args[2]
        assert field == "submitted_at"
        # Credentials must NOT appear in response
        assert "username" not in resp.text
        assert "password" not in resp.text
        app_inst.dependency_overrides.clear()


@pytest.mark.anyio
async def test_landing_page_returns_html():
    """GET /phishing/landing/{token} returns HTML with a login form."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        app_inst = _setup_app()
        recipient = _make_recipient()
        with patch.object(svc, "record_tracking_event", AsyncMock(return_value=recipient)):
            from httpx import ASGITransport, AsyncClient
            async with AsyncClient(transport=ASGITransport(app=app_inst), base_url="http://test") as ac:
                resp = await ac.get("/phishing/landing/tok789")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "<form" in resp.text
        app_inst.dependency_overrides.clear()
