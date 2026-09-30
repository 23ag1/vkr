import inspect
from importlib import reload
from unittest.mock import patch

from tests.conftest import BASE_ENV


def test_get_db_dependency_exists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.deps as deps_module
        reload(deps_module)
        assert hasattr(deps_module, "get_db")
        assert inspect.isasyncgenfunction(deps_module.get_db)


def test_get_current_user_exists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.deps as deps_module
        reload(deps_module)
        assert hasattr(deps_module, "get_current_user")
        assert callable(deps_module.get_current_user)


def test_get_current_admin_exists():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        import app.deps as deps_module
        reload(deps_module)
        assert hasattr(deps_module, "get_current_admin")
        assert callable(deps_module.get_current_admin)
