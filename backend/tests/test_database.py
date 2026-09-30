import inspect
from importlib import reload
from unittest.mock import patch

from tests.conftest import BASE_ENV


def test_async_engine_created():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.database as db_module
        reload(db_module)
        assert db_module.engine is not None


def test_async_session_factory_exists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.database as db_module
        reload(db_module)
        assert db_module.AsyncSessionLocal is not None


def test_get_db_is_async_generator():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.database as db_module
        reload(db_module)
        assert inspect.isasyncgenfunction(db_module.get_db)
