import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import BASE_ENV


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


def _make_dept():
    d = MagicMock()
    d.id = uuid.uuid4()
    d.name = "Engineering"
    d.parent_id = None
    return d


@pytest.mark.anyio
async def test_list_departments_returns_list():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.department as svc
        reload(svc)

        depts = [_make_dept(), _make_dept()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = depts
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.list_departments(db)
        assert result == depts


@pytest.mark.anyio
async def test_get_department_found():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.department as svc
        reload(svc)

        dept = _make_dept()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dept
        db = _mock_db()
        db.execute.return_value = mock_result

        result = await svc.get_department(db, dept.id)
        assert result is dept


@pytest.mark.anyio
async def test_get_department_not_found_raises_404():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.department as svc
        reload(svc)
        from fastapi import HTTPException

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db = _mock_db()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await svc.get_department(db, uuid.uuid4())
        assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_create_department_persists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.department as svc
        reload(svc)
        from app.schemas.department import DepartmentCreate

        db = _mock_db()
        data = DepartmentCreate(name="Finance")
        await svc.create_department(db, data)
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.name == "Finance"


@pytest.mark.anyio
async def test_update_department_changes_name():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.department as svc
        reload(svc)
        from app.schemas.department import DepartmentUpdate

        dept = _make_dept()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dept
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.update_department(db, dept.id, DepartmentUpdate(name="NewName"))
        assert dept.name == "NewName"


@pytest.mark.anyio
async def test_delete_department_calls_delete():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from importlib import reload
        import app.services.department as svc
        reload(svc)

        dept = _make_dept()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dept
        db = _mock_db()
        db.execute.return_value = mock_result

        await svc.delete_department(db, dept.id)
        db.delete.assert_called_once_with(dept)
