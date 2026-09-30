import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_user(role="employee"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = True
    return u


def _make_question_orm():
    q = MagicMock()
    q.id = uuid.uuid4()
    q.module_id = uuid.uuid4()
    q.text = "What is phishing?"
    q.options = ["A scam", "A fish", "An OS", "A tool"]
    q.correct_index = 0
    q.explanation = "Phishing is a social engineering attack."
    return q


def _setup_app(role="employee"):
    from importlib import reload
    import app.main as main_module

    reload(main_module)
    from app import deps

    user = _make_user(role)

    async def fake_db():
        yield AsyncMock()

    async def fake_current_user():
        return user

    main_module.app.dependency_overrides[deps.get_db] = fake_db
    main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user
    return main_module.app, user


@pytest.mark.anyio
async def test_generate_question_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.testing as svc

        app_inst, _ = _setup_app("employee")
        question = _make_question_orm()
        with patch.object(
            svc, "generate_and_persist_question", AsyncMock(return_value=question)
        ):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/api/testing/generate", json={"module_id": str(question.module_id)}
                )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["text"] == "What is phishing?"
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_submit_answer_correct_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.testing as svc

        app_inst, user = _setup_app("employee")
        feedback = {"is_correct": True, "explanation": "Correct!", "correct_index": 0}
        with patch.object(svc, "submit_answer", AsyncMock(return_value=feedback)):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/api/testing/answer",
                    json={
                        "question_id": str(uuid.uuid4()),
                        "selected_index": 0,
                    },
                )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_correct"] is True
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_submit_answer_out_of_range_index_returns_422_end_to_end():
    # Exercises the REAL runtime path: router -> real testing.submit_answer ->
    # bounds-check -> FastAPI exception handler. submit_answer is NOT mocked.
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.testing as svc

        reload(svc)
        from app import deps

        import app.main as main_module

        reload(main_module)
        user = _make_user("employee")
        question = _make_question_orm()  # 4 options -> valid 0..3

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = question
        db = AsyncMock()
        db.execute.return_value = scalar_result
        db.add = MagicMock()

        async def fake_db():
            yield db

        async def fake_current_user():
            return user

        main_module.app.dependency_overrides[deps.get_db] = fake_db
        main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user

        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=main_module.app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/testing/answer",
                json={
                    "question_id": str(question.id),
                    "selected_index": 99,
                },
            )
        main_module.app.dependency_overrides.clear()

        assert resp.status_code == 422
        db.add.assert_not_called()  # short-circuits before any DB write


@pytest.mark.anyio
async def test_get_history_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.testing as svc

        app_inst, user = _setup_app("employee")
        with patch.object(svc, "get_history", AsyncMock(return_value=[])):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.get("/api/testing/history")
        assert resp.status_code == 200
        from app.main import app

        app.dependency_overrides.clear()
