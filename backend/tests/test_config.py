import pytest
from unittest.mock import patch


def test_settings_database_url_built_from_parts():
    env = {
        "POSTGRES_HOST": "testhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "testdb",
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
        "SECRET_KEY": "a" * 32,
        "OPENAI_API_KEY": "sk-test",
    }
    with patch.dict("os.environ", env, clear=True):
        from importlib import reload
        import app.config as cfg_module
        reload(cfg_module)
        settings = cfg_module.get_settings()

        assert settings.POSTGRES_HOST == "testhost"
        assert settings.POSTGRES_DB == "testdb"
        url = settings.database_url
        assert "testhost" in url
        assert "testdb" in url
        assert url.startswith("postgresql+asyncpg://")


def test_settings_async_url_scheme():
    env = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "vkr",
        "POSTGRES_USER": "vkr",
        "POSTGRES_PASSWORD": "pass",
        "SECRET_KEY": "b" * 32,
        "OPENAI_API_KEY": "sk-test",
    }
    with patch.dict("os.environ", env, clear=True):
        from importlib import reload
        import app.config as cfg_module
        reload(cfg_module)
        s = cfg_module.get_settings()
        assert "asyncpg" in s.database_url


def test_settings_allowed_origins_parsed():
    env = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "vkr",
        "POSTGRES_USER": "vkr",
        "POSTGRES_PASSWORD": "pass",
        "SECRET_KEY": "c" * 32,
        "OPENAI_API_KEY": "sk-test",
        "ALLOWED_ORIGINS": "http://localhost:5173,http://localhost:3000",
    }
    with patch.dict("os.environ", env, clear=True):
        from importlib import reload
        import app.config as cfg_module
        reload(cfg_module)
        s = cfg_module.get_settings()
        assert isinstance(s.allowed_origins, list)
        assert len(s.allowed_origins) == 2
        assert "http://localhost:5173" in s.allowed_origins
