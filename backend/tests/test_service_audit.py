import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


# ── helpers ────────────────────────────────────────────────────────────────


def _make_log(action: str = "login", user_id=None, days_ago: int = 0):
    log = MagicMock()
    log.id = uuid.uuid4()
    log.user_id = user_id or uuid.uuid4()
    log.action = action
    log.details = {"x": 1}
    log.ip_address = "127.0.0.1"
    log.created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return log


# ── write() ────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_write_persists_audit_log():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        db.add = MagicMock()  # add is sync
        db.commit = AsyncMock()

        user_id = uuid.uuid4()
        await svc.write(
            db, user_id=user_id, action="module_completed", details={"module_id": "abc"}
        )

        assert db.add.called
        added = db.add.call_args.args[0]
        assert added.user_id == user_id
        assert added.action == "module_completed"
        assert added.details == {"module_id": "abc"}
        assert db.commit.await_count == 1


@pytest.mark.anyio
async def test_write_handles_none_user_id():
    """Anonymous events (e.g., phishing tracking by token only) — user_id may be None."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        await svc.write(
            db, user_id=None, action="phishing_opened", details={"token": "xyz"}
        )

        added = db.add.call_args.args[0]
        assert added.user_id is None
        assert added.action == "phishing_opened"


@pytest.mark.anyio
async def test_write_commit_false_flushes_not_commits():
    """Shared-transaction mode: the row is flushed (caller owns the single
    commit) so the audit row and its triggering action persist atomically."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()

        await svc.write(
            db, user_id=uuid.uuid4(), action="document_deleted", commit=False
        )

        assert db.add.called
        assert db.flush.await_count == 1
        assert db.commit.await_count == 0  # caller owns the commit


@pytest.mark.anyio
async def test_write_commit_false_propagates_errors():
    """Atomicity guarantee: in shared-transaction mode a failed audit insert
    MUST raise so the whole transaction rolls back — never a silent gap that
    leaves the action committed without its audit row (ФСТЭК-21)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock(side_effect=RuntimeError("constraint violation"))
        db.commit = AsyncMock()

        with pytest.raises(RuntimeError):
            await svc.write(
                db, user_id=uuid.uuid4(), action="document_deleted", commit=False
            )


@pytest.mark.anyio
async def test_write_swallows_db_error():
    """Audit MUST NOT break main flow — if write fails, log but don't raise."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        db.add = MagicMock(side_effect=RuntimeError("db down"))
        db.commit = AsyncMock()

        # Should not raise
        await svc.write(db, user_id=uuid.uuid4(), action="test")


# ── list_logs() ────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_list_logs_returns_paginated_records():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        logs = [_make_log("login"), _make_log("module_completed")]
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = logs
        db.execute = AsyncMock(return_value=result)

        out = await svc.list_logs(db, page=1, limit=20)
        assert out == logs
        # ensure execute was called (query built)
        assert db.execute.await_count == 1


@pytest.mark.anyio
async def test_list_logs_applies_action_filter():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)

        await svc.list_logs(db, action="login")
        # query was built — we don't assert SQL structure, just that filter is accepted
        assert db.execute.await_count == 1


@pytest.mark.anyio
async def test_list_logs_applies_user_filter():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)

        await svc.list_logs(db, user_id=uuid.uuid4())
        assert db.execute.await_count == 1


@pytest.mark.anyio
async def test_list_logs_applies_date_range():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)

        now = datetime.now(timezone.utc)
        await svc.list_logs(db, date_from=now - timedelta(days=7), date_to=now)
        assert db.execute.await_count == 1


# ── export_csv() ────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_export_csv_returns_csv_string():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.audit as svc

        reload(svc)

        logs = [_make_log("login"), _make_log("module_completed")]
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = logs
        db.execute = AsyncMock(return_value=result)

        csv_text = await svc.export_csv(db)
        # CSV header + 2 rows
        lines = csv_text.strip().splitlines()
        assert len(lines) == 3
        assert "action" in lines[0]
        assert "user_id" in lines[0]
        assert "created_at" in lines[0]
        assert "login" in lines[1] or "login" in lines[2]
