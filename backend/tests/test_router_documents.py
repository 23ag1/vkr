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


def _make_user(role="admin"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.is_active = True
    return u


def _setup_app(role="admin"):
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
    return main_module.app


@pytest.mark.anyio
async def test_list_documents_admin_200():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.documents as svc

        app_inst = _setup_app("admin")
        with patch.object(
            svc, "list_documents", AsyncMock(return_value=[_make_doc_orm()])
        ):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.get("/api/documents")
        assert resp.status_code == 200
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_documents_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app_inst), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/documents")
        assert resp.status_code == 403
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_upload_document_admin_201():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.documents as svc

        app_inst = _setup_app("admin")
        doc = _make_doc_orm()
        with patch.object(svc, "upload_document", AsyncMock(return_value=doc)):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/api/documents/upload",
                    data={"title": "Policy"},
                    files={"file": ("policy.txt", b"content here", "text/plain")},
                )
        assert resp.status_code == 201
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_document_admin_200_writes_audit():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.documents as svc
        import app.services.audit as audit_svc

        app_inst = _setup_app("admin")
        doc_id = uuid.uuid4()
        with (
            patch.object(svc, "delete_document", AsyncMock(return_value=None)),
            patch.object(
                audit_svc, "write", AsyncMock(return_value=None)
            ) as mock_write,
        ):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.delete(f"/api/documents/{doc_id}")
        assert resp.status_code == 200
        mock_write.assert_awaited_once()
        kwargs = mock_write.await_args.kwargs
        assert kwargs["action"] == "document_deleted"
        assert kwargs["details"]["document_id"] == str(doc_id)
        assert kwargs["user_id"] is not None
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_document_is_atomic_single_commit():
    """The delete action and its audit row share ONE transaction: the service
    and audit run with commit=False and the router owns the single db.commit()
    — so a crash can never leave the doc deleted without an audit row."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.main as main_module

        reload(main_module)
        from app import deps
        import app.services.documents as svc
        import app.services.audit as audit_svc

        captured = AsyncMock()
        calls = []
        captured.commit = AsyncMock(side_effect=lambda: calls.append("commit"))

        async def fake_db():
            yield captured

        async def fake_current_user():
            return _make_user("admin")

        main_module.app.dependency_overrides[deps.get_db] = fake_db
        main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user

        doc_id = uuid.uuid4()

        async def fake_delete(db, did, *, commit=True):
            calls.append(("delete", commit))

        async def fake_audit(db, **kwargs):
            calls.append(("audit", kwargs.get("commit")))

        with (
            patch.object(svc, "delete_document", side_effect=fake_delete),
            patch.object(audit_svc, "write", side_effect=fake_audit),
        ):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=main_module.app), base_url="http://test"
            ) as ac:
                resp = await ac.delete(f"/api/documents/{doc_id}")

        main_module.app.dependency_overrides.clear()

        assert resp.status_code == 200
        # exactly one commit, and it happens AFTER both the delete and the audit
        assert captured.commit.await_count == 1
        assert calls == [("delete", False), ("audit", False), "commit"]


@pytest.mark.anyio
async def test_upload_document_is_atomic_single_commit():
    """Upload + its audit row share ONE transaction: service and audit run with
    commit=False, the router owns the single db.commit()."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.main as main_module

        reload(main_module)
        from app import deps
        import app.services.documents as svc
        import app.services.audit as audit_svc

        captured = AsyncMock()
        calls = []
        captured.commit = AsyncMock(side_effect=lambda: calls.append("commit"))

        async def fake_db():
            yield captured

        async def fake_current_user():
            return _make_user("admin")

        main_module.app.dependency_overrides[deps.get_db] = fake_db
        main_module.app.dependency_overrides[deps.get_current_user] = fake_current_user

        doc = _make_doc_orm()

        async def fake_upload(db, **kwargs):
            calls.append(("upload", kwargs.get("commit")))
            return doc

        async def fake_audit(db, **kwargs):
            calls.append(("audit", kwargs.get("commit")))

        with (
            patch.object(svc, "upload_document", side_effect=fake_upload),
            patch.object(audit_svc, "write", side_effect=fake_audit),
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
        assert captured.commit.await_count == 1
        assert calls == [("upload", False), ("audit", False), "commit"]


@pytest.mark.anyio
async def test_upload_document_rejects_control_char_title_422():
    """A title with control chars / over max length is a clean 422 at the HTTP
    boundary (log-injection hardening, CWE-117) — not a 500."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.services.documents as svc

        app_inst = _setup_app("admin")
        with patch.object(
            svc, "upload_document", AsyncMock(return_value=_make_doc_orm())
        ):
            from httpx import ASGITransport, AsyncClient

            async with AsyncClient(
                transport=ASGITransport(app=app_inst), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/api/documents/upload",
                    data={"title": "x" * 5000},
                    files={"file": ("policy.txt", b"content here", "text/plain")},
                )
        assert resp.status_code == 422
        from app.main import app

        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_delete_document_employee_403():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        app_inst = _setup_app("employee")
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app_inst), base_url="http://test"
        ) as ac:
            resp = await ac.delete(f"/api/documents/{uuid.uuid4()}")
        assert resp.status_code == 403
        from app.main import app

        app.dependency_overrides.clear()
