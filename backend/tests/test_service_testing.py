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


def _make_module_orm():
    m = MagicMock()
    m.id = uuid.uuid4()
    m.title = "Phishing Basics"
    m.content_md = "# Phishing content here"
    return m


def _make_question_orm():
    q = MagicMock()
    q.id = uuid.uuid4()
    q.module_id = uuid.uuid4()
    q.text = "What is phishing?"
    q.options = ["A scam", "A fish", "An OS", "A tool"]
    q.correct_index = 0
    q.explanation = "Phishing is a social engineering attack."
    return q


@pytest.mark.anyio
async def test_generate_and_persist_question():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)
        import app.services.llm as llm_svc
        import app.services.module as mod_svc

        reload(llm_svc)
        reload(mod_svc)

        module = _make_module_orm()
        question_schema = MagicMock()
        question_schema.text = "Q?"
        question_schema.options = ["A", "B", "C", "D"]
        question_schema.correct_index = 0
        question_schema.explanation = "Because A."

        db = _mock_db()
        db.refresh = AsyncMock(side_effect=lambda q: None)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        db.execute.return_value = mock_result

        with (
            patch.object(mod_svc, "get_module", AsyncMock(return_value=module)),
            patch.object(
                llm_svc, "generate_question", AsyncMock(return_value=question_schema)
            ),
        ):
            result = await svc.generate_and_persist_question(db, module.id)

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.text == "Q?"
        assert added.module_id == module.id


@pytest.mark.anyio
async def test_submit_answer_correct():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)

        question = _make_question_orm()
        question.correct_index = 1
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = question
        db = _mock_db()
        db.execute.return_value = mock_result

        user_id = uuid.uuid4()
        result = await svc.submit_answer(db, user_id, question.id, selected_index=1)

        assert result["is_correct"] is True
        assert db.add.call_count >= 1  # UserAnswer + optional audit log


@pytest.mark.anyio
async def test_submit_answer_wrong_generates_explanation():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)
        import app.services.llm as llm_svc

        question = _make_question_orm()
        question.correct_index = 0
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = question
        db = _mock_db()
        db.execute.return_value = mock_result

        with patch.object(
            llm_svc, "generate_explanation", AsyncMock(return_value="Because phishing.")
        ):
            result = await svc.submit_answer(
                db, uuid.uuid4(), question.id, selected_index=2
            )

        assert result["is_correct"] is False
        assert "explanation" in result


@pytest.mark.anyio
async def test_submit_answer_question_not_found():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.submit_answer(db, uuid.uuid4(), uuid.uuid4(), selected_index=0)
        assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_submit_answer_index_too_high_returns_422():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)
        from fastapi import HTTPException

        question = _make_question_orm()  # 4 options -> valid 0..3
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = question
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.submit_answer(db, uuid.uuid4(), question.id, selected_index=4)
        assert exc.value.status_code == 422
        db.add.assert_not_called()


@pytest.mark.anyio
async def test_submit_answer_negative_index_returns_422():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)
        from fastapi import HTTPException

        question = _make_question_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = question
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.submit_answer(db, uuid.uuid4(), question.id, selected_index=-1)
        assert exc.value.status_code == 422
        db.add.assert_not_called()


@pytest.mark.anyio
async def test_get_history_returns_list():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)

        answers = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = answers
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.get_history(db, uuid.uuid4())
        assert result == answers
