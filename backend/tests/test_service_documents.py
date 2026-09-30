import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _make_doc_orm():
    d = MagicMock()
    d.id = uuid.uuid4()
    d.title = "Security Policy"
    d.source = "upload"
    d.module_id = None
    return d


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.anyio
async def test_upload_document_does_not_write_audit():
    """The router owns the document_uploaded audit row (attributed to the
    current user). The service must NOT write a second, mis-attributed
    (user_id=None) row — that produced duplicate audit entries per upload."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.documents as svc

        reload(svc)

        doc = _make_doc_orm()
        db = _mock_db()
        with (
            patch.object(
                svc.rag_service, "ingest_document", AsyncMock(return_value=doc)
            ),
            patch("app.services.audit.write", AsyncMock()) as audit_write,
        ):
            result = await svc.upload_document(
                db, title="Policy", content="some content", source="policy.txt"
            )

        assert result is doc
        audit_write.assert_not_called()


def _make_user(role="admin"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = True
    return u


@pytest.mark.anyio
async def test_upload_writes_single_audit_row_end_to_end():
    """Real router -> real service path: exactly ONE document_uploaded audit
    row per upload, attributed to the authenticated user (not user_id=None)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.main as main_module

        reload(main_module)
        from app import deps

        user = _make_user("admin")

        async def fake_db():
            yield AsyncMock()

        async def fake_current_user():
            return user

        main_module.app.dependency_overrides[deps.get_db] = fake_db
        main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user

        doc = _make_doc_orm()
        with (
            patch("app.services.rag.ingest_document", AsyncMock(return_value=doc)),
            patch("app.services.audit.write", AsyncMock()) as audit_write,
        ):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=main_module.app), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/api/documents/upload",
                    data={"title": "Policy"},
                    files={"file": ("policy.txt", b"content here", "text/plain")},
                )

        main_module.app.dependency_overrides.clear()

        assert resp.status_code == 201
        # exactly one audit write, attributed to the real user
        assert audit_write.call_count == 1
        _, kwargs = audit_write.call_args
        assert kwargs["action"] == "document_uploaded"
        assert kwargs["user_id"] == user.id
