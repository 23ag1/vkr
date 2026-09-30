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


def _make_module_orm(published=False):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.title = "Phishing Basics"
    m.description = "Learn phishing"
    m.content_md = "# Content"
    m.target_roles = ["employee"]
    m.order_index = 0
    m.is_published = published
    return m


@pytest.mark.anyio
async def test_list_modules_role_filter_in_query_for_employee():
    """Employee query must include target_roles filter."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        captured = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db = _mock_db()

        async def capture_execute(stmt, *args, **kwargs):
            captured.append(stmt)
            return mock_result

        db.execute = capture_execute

        await svc.list_modules(db, role="employee")

        assert len(captured) == 1
        from sqlalchemy.dialects import postgresql
        sql = str(captured[0].compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert "target_roles" in sql


@pytest.mark.anyio
async def test_list_modules_no_role_filter_for_admin():
    """Admin query must NOT include target_roles filter."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        captured = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db = _mock_db()

        async def capture_execute(stmt, *args, **kwargs):
            captured.append(stmt)
            return mock_result

        db.execute = capture_execute

        await svc.list_modules(db, role="admin")

        from sqlalchemy.dialects import postgresql
        sql = str(captured[0].compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert "cardinality" not in sql and "array_position" not in sql


@pytest.mark.anyio
async def test_list_modules_returns_all_for_admin():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        modules = [_make_module_orm(True), _make_module_orm(False)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = modules
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.list_modules(db, role="admin")
        assert result == modules


@pytest.mark.anyio
async def test_list_modules_returns_published_for_employee():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        published = _make_module_orm(True)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [published]
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.list_modules(db, role="employee")
        assert result == [published]


@pytest.mark.anyio
async def test_get_module_found():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        module = _make_module_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = module
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.get_module(db, module.id)
        assert result is module


@pytest.mark.anyio
async def test_get_module_not_found_raises_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.get_module(db, uuid.uuid4())
        assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_create_module_persists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)
        from app.schemas.module import ModuleCreate

        data = ModuleCreate(
            title="Phishing Basics",
            description="Learn phishing",
            content_md="# Content",
            target_roles=["employee"],
            order_index=1,
        )
        db = _mock_db()
        db.refresh = AsyncMock(side_effect=lambda m: None)

        module = await svc.create_module(db, data)
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.title == "Phishing Basics"
        assert added.is_published is False


@pytest.mark.anyio
async def test_update_module_applies_changes():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)
        from app.schemas.module import ModuleUpdate

        module = _make_module_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = module
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.update_module(db, module.id, ModuleUpdate(title="Updated"))
        assert module.title == "Updated"


@pytest.mark.anyio
async def test_publish_module_sets_published():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        module = _make_module_orm(False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = module
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.publish_module(db, module.id)
        assert result.is_published is True


@pytest.mark.anyio
async def test_delete_module_calls_delete():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        module = _make_module_orm()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = module
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.delete_module(db, module.id)
        db.delete.assert_called_once_with(module)


@pytest.mark.anyio
async def test_list_modules_role_filter_applied_for_employee():
    """Employee query must include target_roles array filter in WHERE clause."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.list_modules(db, role="employee")

        query = db.execute.call_args[0][0]
        sql = str(query.compile(compile_kwargs={"literal_binds": True}))
        # cardinality() or @> (contains) should appear to filter by role
        assert "cardinality" in sql or "@>" in sql or "employee" in sql.upper().replace("SELECT", "")


@pytest.mark.anyio
async def test_list_modules_admin_sees_all_no_role_filter():
    """Admin query must NOT include cardinality/array-contains filter."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.list_modules(db, role="admin")

        query = db.execute.call_args[0][0]
        sql = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "cardinality" not in sql and "@>" not in sql


@pytest.mark.anyio
async def test_list_modules_security_specialist_sees_all_no_role_filter():
    """security_specialist bypasses role filter (same as admin)."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.module as svc
        reload(svc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.list_modules(db, role="security_specialist")

        query = db.execute.call_args[0][0]
        sql = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "cardinality" not in sql and "@>" not in sql
