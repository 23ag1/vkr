"""Tests for adaptive diagnostic service (vkr-nif)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import BASE_ENV


def _make_session(answers=None, count=0):
    s = MagicMock()
    s.id = uuid.uuid4()
    s.user_id = uuid.uuid4()
    s.answers = answers or []
    s.question_count = count
    s.is_finished = False
    return s


def _make_question_orm(topic="phishing"):
    q = MagicMock()
    q.id = uuid.uuid4()
    q.module_id = uuid.uuid4()
    q.text = f"Question about {topic}?"
    q.options = ["A", "B", "C", "D"]
    q.correct_index = 0
    q.explanation = "Because A."
    return q


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.anyio
async def test_compute_profile_correct_scores():
    """Score per topic = correct / total; topics with no answers default to 0."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc

        reload(svc)

        answers = [
            {"topic": "passwords", "is_correct": True},
            {"topic": "passwords", "is_correct": False},
            {"topic": "passwords", "is_correct": False},
            {"topic": "phishing", "is_correct": True},
            {"topic": "phishing", "is_correct": True},
        ]
        scores = svc.compute_profile(answers)

        assert abs(scores["passwords"] - 1 / 3) < 0.01
        assert abs(scores["phishing"] - 1.0) < 0.01
        # Topics not in answers default to 0
        for topic in svc.TOPICS:
            if topic not in ("passwords", "phishing"):
                assert scores[topic] == 0.0


@pytest.mark.anyio
async def test_compute_profile_weak_passwords():
    """5 wrong + 5 right for passwords → score < 0.5 (the AC test scenario)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc

        reload(svc)

        answers = [{"topic": "passwords", "is_correct": i < 5} for i in range(10)]
        scores = svc.compute_profile(answers)
        assert scores["passwords"] == 0.5  # exactly 0.5 when equal

        answers_5_wrong = [{"topic": "passwords", "is_correct": False}] * 5 + [
            {"topic": "other", "is_correct": True}
        ] * 5
        answers_5_wrong[5]["topic"] = "phishing"
        answers_5_wrong[6]["topic"] = "phishing"
        answers_5_wrong[7]["topic"] = "phishing"
        answers_5_wrong[8]["topic"] = "phishing"
        answers_5_wrong[9]["topic"] = "phishing"

        scores2 = svc.compute_profile(answers_5_wrong)
        assert scores2["passwords"] == 0.0  # all wrong → 0


@pytest.mark.anyio
async def test_select_topic_prefers_weak():
    """Topic selection should pick the topic with the lowest score."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc

        reload(svc)

        scores = {t: 1.0 for t in svc.TOPICS}
        scores["incident_response"] = 0.0  # weakest
        topic = svc.select_topic(scores, history=[])
        assert topic == "incident_response"


@pytest.mark.anyio
async def test_select_topic_avoids_recent_repeat():
    """When all scores equal, avoid the most recently asked topic."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc

        reload(svc)

        scores = {t: 0.5 for t in svc.TOPICS}
        history = [{"topic": "phishing"}]
        topic = svc.select_topic(scores, history)
        assert topic != "phishing"


@pytest.mark.anyio
async def test_finish_assigns_modules_for_weak_topics():
    """finish() must auto-assign modules for all topics with score < 0.5."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc
        import app.services.learning as learn_svc

        reload(svc)
        reload(learn_svc)

        user_id = uuid.uuid4()
        session = _make_session(
            answers=[
                {"topic": "passwords", "is_correct": False},
                {"topic": "passwords", "is_correct": False},
                {"topic": "phishing", "is_correct": True},
            ],
            count=3,
        )
        session.is_finished = False

        # finish_session(commit=True, scores=None) issues 4 query kinds in order:
        # 1) session lookup, 2) existing competency profiles, 3) user (to mark
        # diagnostic_completed_at), 4+) module lookups per weak topic.
        sess_res = MagicMock()
        sess_res.scalar_one_or_none.return_value = session

        profiles_res = MagicMock()
        profiles_res.scalars.return_value.all.return_value = []  # no existing profiles

        user = MagicMock()
        user_res = MagicMock()
        user_res.scalar_one_or_none.return_value = user

        passwords_module = MagicMock()
        passwords_module.id = uuid.uuid4()
        mod_res = MagicMock()
        mod_res.scalars.return_value.all.return_value = [passwords_module]

        call_count = 0

        async def mock_execute(stmt, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return sess_res
            if call_count == 2:
                return profiles_res
            if call_count == 3:
                return user_res
            return mod_res  # module lookups

        db = _mock_db()
        db.execute = mock_execute

        with patch.object(learn_svc, "assign_module", AsyncMock()) as mock_assign:
            await svc.finish_session(db, session_id=session.id, user_id=user_id)

        # legacy commit=True path: new profiles staged, user marked, single commit
        assert db.add.called  # UserCompetencyProfile rows added
        assert user.diagnostic_completed_at is not None
        assert db.commit.await_count == 1

        # passwords score = 0/2 = 0.0 → should assign
        mock_assign.assert_called()
        called_module_ids = {
            call.kwargs.get("module_id") for call in mock_assign.call_args_list
        }
        assert passwords_module.id in called_module_ids


def _make_question_for_submit(correct_index=0):
    q = MagicMock()
    q.id = uuid.uuid4()
    q.correct_index = correct_index
    q.options = ["A", "B", "C", "D"]
    return q


@pytest.mark.anyio
async def test_finish_session_commit_false_defers_commit_and_assign(monkeypatch):
    """commit=False: finish_session upserts profile + marks user but must NOT
    commit and must NOT auto-assign — the caller owns the single atomic commit
    and runs auto-assign afterwards."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc

        reload(svc)

        user_id = uuid.uuid4()
        scores = {t: 0.0 for t in svc.TOPICS}

        # No existing profiles, user lookup returns a user
        empty = MagicMock()
        empty.scalars.return_value.all.return_value = []
        user_res = MagicMock()
        user_res.scalar_one_or_none.return_value = MagicMock()

        results = [empty, user_res]

        async def mock_execute(stmt, *args, **kwargs):
            return results.pop(0)

        db = _mock_db()
        db.execute = mock_execute

        assign_mock = AsyncMock()
        monkeypatch.setattr(svc, "_auto_assign_modules", assign_mock)

        out = await svc.finish_session(
            db, session_id=uuid.uuid4(), user_id=user_id, scores=scores, commit=False
        )

        assert out == scores
        assert db.commit.await_count == 0  # caller owns the commit
        assign_mock.assert_not_awaited()  # auto-assign deferred to caller


@pytest.mark.anyio
async def test_submit_answer_finish_audits_atomically(monkeypatch):
    """On the finishing answer, diagnostic_completed audit must share ONE
    transaction with finish_session's mutations: a single db.commit() that
    owns session.is_finished + profile + audit row, with auto-assign after."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc
        import app.services.audit as audit_svc

        reload(svc)

        user_id = uuid.uuid4()
        session = _make_session(
            answers=[{"topic": "phishing", "is_correct": True}] * 9,
            count=9,  # next answer is #10 → finishes
        )
        session.user_id = user_id
        question = _make_question_for_submit(correct_index=0)

        sess_res = MagicMock()
        sess_res.scalar_one_or_none.return_value = session
        q_res = MagicMock()
        q_res.scalar_one_or_none.return_value = question
        results = [sess_res, q_res]

        async def mock_execute(stmt, *args, **kwargs):
            return results.pop(0)

        db = _mock_db()
        db.execute = mock_execute

        order = []
        db.commit = AsyncMock(side_effect=lambda: order.append("commit"))

        async def fake_finish(*a, **kw):
            order.append(("finish", kw.get("commit")))
            return {t: 0.0 for t in svc.TOPICS}

        monkeypatch.setattr(svc, "finish_session", fake_finish)

        audit_mock = AsyncMock(
            side_effect=lambda *a, **kw: order.append(("audit", kw.get("commit")))
        )
        monkeypatch.setattr(audit_svc, "write", audit_mock)
        assign_mock = AsyncMock(side_effect=lambda *a, **kw: order.append("assign"))
        monkeypatch.setattr(svc, "_auto_assign_modules", assign_mock)

        out = await svc.submit_answer(
            db,
            session_id=session.id,
            user_id=user_id,
            question_id=question.id,
            topic="phishing",
            selected_index=0,
        )

        assert out["finished"] is True
        # finish_session called with commit=False (shared transaction)
        assert ("finish", False) in order
        # audit written with commit=False (shared transaction)
        assert ("audit", False) in order
        # exactly ONE commit, and it comes AFTER both finish + audit
        assert order.count("commit") == 1
        commit_idx = order.index("commit")
        assert order.index(("finish", False)) < commit_idx
        assert order.index(("audit", False)) < commit_idx
        # auto-assign runs AFTER the atomic commit (best-effort side-effect)
        assert order.index("assign") > commit_idx


@pytest.mark.anyio
@pytest.mark.parametrize("bad_index", [-1, 4, 99])
async def test_submit_answer_rejects_out_of_range_index(monkeypatch, bad_index):
    """An out-of-range selected_index is invalid input: reject with 422
    (ValidationException) instead of recording a garbage answer (twin of vkr-g2h).
    No answer is appended, the session is untouched, and nothing commits."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc

        reload(svc)

        user_id = uuid.uuid4()
        session = _make_session(answers=[], count=0)
        session.user_id = user_id
        question = _make_question_for_submit(correct_index=0)
        question.options = ["A", "B", "C", "D"]  # len == 4

        sess_res = MagicMock()
        sess_res.scalar_one_or_none.return_value = session
        q_res = MagicMock()
        q_res.scalar_one_or_none.return_value = question
        results = [sess_res, q_res]

        async def mock_execute(stmt, *args, **kwargs):
            return results.pop(0)

        db = _mock_db()
        db.execute = mock_execute

        from app.core.exceptions import ValidationException

        with pytest.raises(type(ValidationException)) as exc_info:
            await svc.submit_answer(
                db,
                session_id=session.id,
                user_id=user_id,
                question_id=question.id,
                topic="phishing",
                selected_index=bad_index,
            )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == ValidationException.detail
        # invalid input is rejected before any state mutation
        assert session.answers == []
        assert session.question_count == 0
        db.commit.assert_not_awaited()


@pytest.mark.anyio
async def test_submit_answer_finish_audit_failure_rolls_back(monkeypatch):
    """Negative control: if the audit insert fails in shared-transaction mode,
    the error MUST propagate (no swallow) so the whole transaction rolls back —
    a completed diagnostic can never commit without its audit row (ФСТЭК-21)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.diagnostic as svc
        import app.services.audit as audit_svc

        reload(svc)

        user_id = uuid.uuid4()
        session = _make_session(
            answers=[{"topic": "phishing", "is_correct": True}] * 9, count=9
        )
        session.user_id = user_id
        question = _make_question_for_submit(correct_index=0)

        sess_res = MagicMock()
        sess_res.scalar_one_or_none.return_value = session
        q_res = MagicMock()
        q_res.scalar_one_or_none.return_value = question
        results = [sess_res, q_res]

        async def mock_execute(stmt, *args, **kwargs):
            return results.pop(0)

        db = _mock_db()
        db.execute = mock_execute

        monkeypatch.setattr(
            svc, "finish_session", AsyncMock(return_value={t: 0.0 for t in svc.TOPICS})
        )
        monkeypatch.setattr(
            audit_svc, "write", AsyncMock(side_effect=RuntimeError("audit boom"))
        )
        assign_mock = AsyncMock()
        monkeypatch.setattr(svc, "_auto_assign_modules", assign_mock)

        with pytest.raises(RuntimeError, match="audit boom"):
            await svc.submit_answer(
                db,
                session_id=session.id,
                user_id=user_id,
                question_id=question.id,
                topic="phishing",
                selected_index=0,
            )

        # the final atomic commit never ran, and no modules were assigned
        assert db.commit.await_count == 0
        assign_mock.assert_not_awaited()
