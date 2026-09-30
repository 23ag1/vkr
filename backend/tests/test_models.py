from importlib import reload
from unittest.mock import patch

from tests.conftest import BASE_ENV


def test_base_model_exists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.base as base_module
        reload(base_module)
        assert hasattr(base_module, "Base")
        assert hasattr(base_module, "UUIDMixin")
        assert hasattr(base_module, "TimestampMixin")


def test_department_model():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.department as m
        reload(m)
        cols = {c.key for c in m.Department.__table__.columns}
        assert {"id", "name", "parent_id"}.issubset(cols)


def test_user_model():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.user as m
        reload(m)
        cols = {c.key for c in m.User.__table__.columns}
        assert {"id", "email", "hashed_password", "role", "department_id", "is_active"}.issubset(cols)


def test_module_model():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.module as m
        reload(m)
        cols = {c.key for c in m.Module.__table__.columns}
        assert {"id", "title", "target_roles"}.issubset(cols)


def test_learning_model():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.learning as m
        reload(m)
        cols = {c.key for c in m.UserModuleProgress.__table__.columns}
        assert {"user_id", "module_id", "status"}.issubset(cols)


def test_test_models():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.test as m
        reload(m)
        assert hasattr(m, "Question")
        assert hasattr(m, "UserAnswer")
        q_cols = {c.key for c in m.Question.__table__.columns}
        assert {"module_id", "text", "options", "correct_index"}.issubset(q_cols)


def test_chat_models():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.chat as m
        reload(m)
        assert hasattr(m, "ChatSession")
        assert hasattr(m, "ChatMessage")
        msg_cols = {c.key for c in m.ChatMessage.__table__.columns}
        assert {"role", "content", "sources"}.issubset(msg_cols)


def test_rag_models():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.rag as m
        reload(m)
        assert hasattr(m, "Document")
        assert hasattr(m, "DocumentChunk")
        chunk_cols = {c.key for c in m.DocumentChunk.__table__.columns}
        assert {"embedding", "content"}.issubset(chunk_cols)


def test_phishing_models():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.phishing as m
        reload(m)
        assert hasattr(m, "PhishingTemplate")
        assert hasattr(m, "PhishingCampaign")
        assert hasattr(m, "PhishingRecipient")
        r_cols = {c.key for c in m.PhishingRecipient.__table__.columns}
        assert "tracking_token" in r_cols


def test_audit_model():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models.audit as m
        reload(m)
        cols = {c.key for c in m.AuditLog.__table__.columns}
        assert {"user_id", "action", "details"}.issubset(cols)


def test_models_init_exports_all():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.models as models_module
        reload(models_module)
        expected = [
            "User", "Department", "Module", "UserModuleProgress",
            "Question", "UserAnswer", "ChatSession", "ChatMessage",
            "Document", "DocumentChunk", "PhishingTemplate",
            "PhishingCampaign", "PhishingRecipient", "AuditLog",
        ]
        for name in expected:
            assert hasattr(models_module, name), f"Missing model: {name}"
