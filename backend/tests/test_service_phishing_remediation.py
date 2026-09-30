"""Tests for phishing click → auto-assign corrective module (vkr-l0i)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_recipient(user_id=None, campaign_id=None, token="testtoken"):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.user_id = user_id or uuid.uuid4()
    r.campaign_id = campaign_id or uuid.uuid4()
    r.tracking_token = token
    r.opened_at = None
    r.clicked_at = None
    r.submitted_at = None
    r.reported_at = None
    return r


def _make_module(mid=None, published=True):
    m = MagicMock()
    m.id = mid or uuid.uuid4()
    m.is_published = published
    m.target_roles = ["phishing_remediation"]
    return m


@pytest.mark.anyio
async def test_clicked_at_triggers_remediation_assign():
    """record_tracking_event with 'clicked_at' auto-assigns a remediation module."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        import app.services.learning as learn_svc

        db = AsyncMock()
        recipient = _make_recipient()
        module = _make_module()

        # simulate: first execute → recipient, second → remediation module query result
        result_mock_recipient = MagicMock()
        result_mock_recipient.scalar_one_or_none.return_value = recipient

        result_mock_module = MagicMock()
        result_mock_module.scalar_one_or_none.return_value = module

        result_mock_progress = MagicMock()
        result_mock_progress.scalar_one_or_none.return_value = None  # not yet assigned

        db.execute = AsyncMock(side_effect=[
            result_mock_recipient,
            result_mock_module,
            result_mock_progress,
        ])

        with patch.object(learn_svc, "assign_module", AsyncMock()) as mock_assign:
            await svc.record_tracking_event(db, "testtoken", "clicked_at")

        mock_assign.assert_awaited_once_with(db, recipient.user_id, module.id)


@pytest.mark.anyio
async def test_clicked_at_no_assign_if_already_enrolled():
    """If user already has the remediation module, do NOT assign again."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        import app.services.learning as learn_svc

        db = AsyncMock()
        recipient = _make_recipient()
        module = _make_module()

        existing_progress = MagicMock()  # already enrolled

        result_mock_recipient = MagicMock()
        result_mock_recipient.scalar_one_or_none.return_value = recipient
        result_mock_module = MagicMock()
        result_mock_module.scalar_one_or_none.return_value = module
        result_mock_progress = MagicMock()
        result_mock_progress.scalar_one_or_none.return_value = existing_progress

        db.execute = AsyncMock(side_effect=[
            result_mock_recipient,
            result_mock_module,
            result_mock_progress,
        ])

        with patch.object(learn_svc, "assign_module", AsyncMock()) as mock_assign:
            await svc.record_tracking_event(db, "testtoken", "clicked_at")

        mock_assign.assert_not_awaited()


@pytest.mark.anyio
async def test_open_event_does_not_trigger_remediation():
    """record_tracking_event with 'opened_at' does NOT assign any module."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        import app.services.learning as learn_svc

        db = AsyncMock()
        recipient = _make_recipient()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = recipient
        db.execute = AsyncMock(return_value=result_mock)

        with patch.object(learn_svc, "assign_module", AsyncMock()) as mock_assign:
            await svc.record_tracking_event(db, "testtoken", "opened_at")

        mock_assign.assert_not_awaited()


@pytest.mark.anyio
async def test_tracking_event_audit_is_atomic_single_commit():
    """reported_at: the tracking flag and its audit row share ONE transaction —
    audit runs commit=False and exactly one commit follows the flush (vkr-rhz)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.phishing_campaigns as svc
        import app.services.audit as audit_svc

        db = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        recipient = _make_recipient()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = recipient
        db.execute = AsyncMock(return_value=result_mock)

        audit_kwargs = {}

        async def fake_audit(d, **kwargs):
            audit_kwargs.update(kwargs)

        with patch.object(audit_svc, "write", side_effect=fake_audit):
            await svc.record_tracking_event(db, "testtoken", "reported_at")

        assert audit_kwargs.get("commit") is False
        assert audit_kwargs.get("action") == "phishing_reported"
        assert db.commit.await_count == 1
        assert db.flush.await_count >= 1
