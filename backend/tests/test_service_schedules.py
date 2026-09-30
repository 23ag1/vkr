"""Tests for training schedule service (vkr-ged)."""
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_schedule(sid=None, action="assign_module", cadence="quarterly", module_id=None, is_active=True):
    s = MagicMock()
    s.id = sid or uuid.uuid4()
    s.action = action
    s.cadence = cadence
    s.module_id = module_id or uuid.uuid4()
    s.target_roles = []
    s.last_triggered_at = None
    s.is_active = is_active
    return s


@pytest.mark.anyio
async def test_list_schedules_returns_all():
    """list_schedules returns all schedule records."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.schedules as svc

        db = AsyncMock()
        sched = _make_schedule()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [sched]
        db.execute = AsyncMock(return_value=result_mock)

        schedules = await svc.list_schedules(db)
        assert len(schedules) == 1


@pytest.mark.anyio
async def test_create_schedule_persists():
    """create_schedule adds a new schedule record."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.schedules as svc
        from app.schemas.schedules import ScheduleCreate

        db = AsyncMock()
        body = ScheduleCreate(
            action="assign_module",
            cadence="quarterly",
            module_id=uuid.uuid4(),
            target_roles=["employee"],
        )
        result = await svc.create_schedule(db, body)
        assert db.add.called
        assert db.commit.called


@pytest.mark.anyio
async def test_trigger_schedule_calls_assign():
    """trigger_schedule with assign_module action calls learning_service.assign_module for users."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.schedules as svc
        import app.services.learning as learn_svc

        db = AsyncMock()
        module_id = uuid.uuid4()
        user_id = uuid.uuid4()
        sched = _make_schedule(action="assign_module", module_id=module_id)

        # DB calls: get schedule, get users matching roles, existing progress check
        result_sched = MagicMock()
        result_sched.scalar_one_or_none.return_value = sched

        user_mock = MagicMock()
        user_mock.id = user_id
        result_users = MagicMock()
        result_users.scalars.return_value.all.return_value = [user_mock]

        result_progress = MagicMock()
        result_progress.scalar_one_or_none.return_value = None  # not yet assigned

        db.execute = AsyncMock(side_effect=[result_sched, result_users, result_progress])

        with patch.object(learn_svc, "assign_module", AsyncMock()) as mock_assign:
            summary = await svc.trigger_schedule(db, sched.id)

        mock_assign.assert_awaited_once()
        assert summary["assigned"] == 1
