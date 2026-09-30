"""Tests for social engineering simulation service (vkr-4sm, Scenario 4 VKR)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_session(session_id=None, user_id=None):
    s = MagicMock()
    s.id = session_id or uuid.uuid4()
    s.user_id = user_id or uuid.uuid4()
    s.title = "[sim] IT Support Call"
    return s


@pytest.mark.anyio
async def test_get_scenarios_returns_list():
    """get_scenarios returns non-empty list of scenario dicts with id and title."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from app.services.social_eng_sim import get_scenarios
        scenarios = get_scenarios()
        assert len(scenarios) >= 1
        assert "id" in scenarios[0]
        assert "title" in scenarios[0]


@pytest.mark.anyio
async def test_start_simulation_creates_session():
    """start_simulation creates a chat session and returns first attacker message."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from app.services import social_eng_sim as svc

        db = AsyncMock()
        user_id = uuid.uuid4()
        session = _make_session(user_id=user_id)

        db.refresh = AsyncMock()

        with patch("app.services.llm.chat_completion", AsyncMock(return_value="Hello, this is IT support...")):
            result = await svc.start_simulation(db, user_id=user_id, scenario_id="it_support")

        assert db.add.called
        assert db.commit.called
        assert "content" in result
        assert len(result["content"]) > 0


@pytest.mark.anyio
async def test_simulation_turn_returns_score():
    """simulation_turn evaluates user response and returns score in sources."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from app.services import social_eng_sim as svc

        db = AsyncMock()
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        session = _make_session(session_id=session_id, user_id=user_id)

        result_session = MagicMock()
        result_session.scalar_one_or_none.return_value = session

        result_history = MagicMock()
        result_history.scalars.return_value.all.return_value = []

        db.execute = AsyncMock(side_effect=[result_session, result_history])

        llm_response = '{"reply": "I see, can you verify your employee ID?", "score": 90, "feedback": "Good job refusing to share your password."}'

        with patch("app.services.llm.chat_completion", AsyncMock(return_value=llm_response)):
            result = await svc.simulation_turn(
                db, session_id=session_id, user_id=user_id,
                user_message="I don't share passwords over the phone."
            )

        assert "content" in result
        assert "score" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100
