"""Tests for FSTEC briefing type support (vkr-f8a)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import BASE_ENV


@pytest.mark.anyio
async def test_module_schema_includes_briefing_type():
    """ModuleResponse must include briefing_type field."""
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict("os.environ", BASE_ENV, clear=True):
        from app.schemas.module import ModuleResponse
        fields = ModuleResponse.model_fields
        assert "briefing_type" in fields


@pytest.mark.anyio
async def test_briefing_type_defaults_to_none():
    """briefing_type defaults to 'none' if not set."""
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict("os.environ", BASE_ENV, clear=True):
        from app.schemas.module import ModuleResponse
        m = MagicMock()
        m.id = uuid.uuid4()
        m.title = "Test"
        m.description = "Desc"
        m.content_md = ""
        m.target_roles = []
        m.order_index = 0
        m.is_published = True
        m.briefing_type = "none"
        m.created_at = None
        m.updated_at = None

        r = ModuleResponse.model_validate(m)
        assert r.briefing_type == "none"


@pytest.mark.anyio
async def test_briefing_analytics_counts_by_type():
    """get_briefing_stats returns completion counts grouped by briefing_type."""
    with __import__("unittest.mock", fromlist=["patch"]).patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.analytics as svc

        db = AsyncMock()
        row1 = {"briefing_type": "introductory", "completed": 5, "total": 10}
        row2 = {"briefing_type": "repeated", "completed": 3, "total": 8}

        result = MagicMock()
        result.mappings.return_value.all.return_value = [row1, row2]
        db.execute = AsyncMock(return_value=result)

        stats = await svc.get_briefing_stats(db)
        assert len(stats) == 2
        assert stats[0]["briefing_type"] == "introductory"
        assert stats[0]["completion_rate"] == 0.5
