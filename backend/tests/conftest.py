import pytest
from unittest.mock import patch

BASE_ENV = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "vkr",
    "POSTGRES_USER": "vkr",
    "POSTGRES_PASSWORD": "testpass",
    "SECRET_KEY": "a" * 32,
    "OPENAI_API_KEY": "sk-test",
}


@pytest.fixture()
def env_patch():
    with patch.dict("os.environ", BASE_ENV, clear=True):
        yield BASE_ENV
