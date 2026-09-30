"""Tests for incident support service (vkr-1vs, Scenario 6 VKR)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


@pytest.mark.anyio
async def test_report_incident_returns_guidance():
    """report_incident returns LLM guidance string."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.incident as svc

        db = AsyncMock()
        user_id = uuid.uuid4()

        with patch("app.services.llm.chat_completion", AsyncMock(return_value="1. Disconnect from network immediately.")):
            result = await svc.report_incident(db, user_id=user_id, description="I clicked a suspicious link")

        assert isinstance(result["guidance"], str)
        assert len(result["guidance"]) > 0
        assert "incident_id" in result


@pytest.mark.anyio
async def test_report_incident_sanitizes_input():
    """report_incident runs description through prompt_guard."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.incident as svc

        db = AsyncMock()

        with (
            patch("app.services.llm.chat_completion", AsyncMock(return_value="guidance")),
            patch("app.services.incident.sanitize_user_input", return_value="clean desc") as mock_san,
        ):
            await svc.report_incident(db, user_id=uuid.uuid4(), description="bad input")

        mock_san.assert_called_once_with("bad input")


@pytest.mark.anyio
async def test_report_incident_writes_audit():
    """report_incident writes an audit event."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.incident as svc
        import app.services.audit as audit_svc

        db = AsyncMock()
        user_id = uuid.uuid4()

        with (
            patch("app.services.llm.chat_completion", AsyncMock(return_value="guidance")),
            patch.object(audit_svc, "write", AsyncMock()) as mock_write,
        ):
            await svc.report_incident(db, user_id=user_id, description="phishing click")

        mock_write.assert_awaited_once()
        call_kwargs = mock_write.call_args.kwargs
        assert call_kwargs["action"] == "incident_reported"
