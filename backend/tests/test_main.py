import pytest
from importlib import reload
from unittest.mock import patch

from tests.conftest import BASE_ENV


def test_app_exists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.main as main_module
        reload(main_module)
        assert main_module.app is not None


@pytest.mark.anyio
async def test_health_endpoint():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.main as main_module
        reload(main_module)
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_cors_headers_present():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.main as main_module
        reload(main_module)
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.options(
                "/health",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                },
            )
    assert resp.status_code in (200, 204)
