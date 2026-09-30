import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_progress_orm(status="not_started"):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.user_id = uuid.uuid4()
    p.module_id = uuid.uuid4()
    p.status = status
    p.score = None
    p.completed_at = None
    return p


@pytest.mark.anyio
async def test_get_my_path_returns_list():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.learning as svc
        reload(svc)

        items = [_make_progress_orm(), _make_progress_orm("completed")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = items
        db = _mock_db()
        db.execute.return_value = mock_result

        user_id = uuid.uuid4()
        result = await svc.get_my_path(db, user_id)
        assert result == items


@pytest.mark.anyio
async def test_assign_module_creates_progress():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.learning as svc
        reload(svc)

        db = _mock_db()
        db.refresh = AsyncMock(side_effect=lambda p: None)

        user_id = uuid.uuid4()
        module_id = uuid.uuid4()
        progress = await svc.assign_module(db, user_id, module_id)
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.user_id == user_id
        assert added.module_id == module_id
        assert added.status == "not_started"


@pytest.mark.anyio
async def test_update_progress_changes_status():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.learning as svc
        reload(svc)
        from app.schemas.learning import ProgressUpdate

        progress = _make_progress_orm("not_started")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = progress
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.update_progress(db, progress.id, ProgressUpdate(status="in_progress"))
        assert progress.status == "in_progress"


@pytest.mark.anyio
async def test_update_progress_not_found_raises_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.learning as svc
        reload(svc)
        from app.schemas.learning import ProgressUpdate
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.update_progress(db, uuid.uuid4(), ProgressUpdate(status="completed"))
        assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_update_progress_completed_sets_completed_at():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.learning as svc
        reload(svc)
        from app.schemas.learning import ProgressUpdate

        progress = _make_progress_orm("in_progress")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = progress
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.update_progress(db, progress.id, ProgressUpdate(status="completed", score=85))
        assert progress.status == "completed"
        assert progress.score == 85
        assert progress.completed_at is not None
