"""Tests for department analytics (vkr-kbv)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import BASE_ENV


@pytest.mark.anyio
async def test_get_departments_returns_list():
    """get_departments_analytics returns a list of per-dept metric dicts."""
    with patch_env():
        import app.services.analytics as svc

        db = AsyncMock()
        row1 = MagicMock()
        row1._mapping = {
            "dept_id": uuid.uuid4(),
            "dept_name": "IT",
            "total_users": 10,
            "completed": 7,
            "total_progress": 10,
            "avg_score": 0.82,
            "clicked": 2,
            "total_recipients": 10,
        }
        result = MagicMock()
        result.mappings.return_value.all.return_value = [row1._mapping]
        db.execute = AsyncMock(return_value=result)

        rows = await svc.get_departments_analytics(db)

        assert len(rows) == 1
        assert rows[0]["name"] == "IT"
        assert rows[0]["completion_rate"] == 0.7
        assert rows[0]["avg_score"] == 0.82
        assert rows[0]["phishing_click_rate"] == 0.2


@pytest.mark.anyio
async def test_get_departments_zero_division_safe():
    """Departments with no users or no progress do not raise ZeroDivisionError."""
    with patch_env():
        import app.services.analytics as svc

        db = AsyncMock()
        row = MagicMock()
        row._mapping = {
            "dept_id": uuid.uuid4(),
            "dept_name": "Empty Dept",
            "total_users": 0,
            "completed": 0,
            "total_progress": 0,
            "avg_score": None,
            "clicked": 0,
            "total_recipients": 0,
        }
        result = MagicMock()
        result.mappings.return_value.all.return_value = [row._mapping]
        db.execute = AsyncMock(return_value=result)

        rows = await svc.get_departments_analytics(db)

        assert rows[0]["completion_rate"] == 0.0
        assert rows[0]["phishing_click_rate"] == 0.0


from contextlib import contextmanager
from unittest.mock import patch

@contextmanager
def patch_env():
    import os
    from tests.conftest import BASE_ENV
    with patch.dict(os.environ, BASE_ENV, clear=True):
        yield
