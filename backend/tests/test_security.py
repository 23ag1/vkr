import pytest
from importlib import reload
from unittest.mock import patch

from tests.conftest import BASE_ENV

_SEC_ENV = {**BASE_ENV, "SECRET_KEY": "supersecretkey_for_testing_32chars"}


def _load_security():
    import app.core.security as sec
    reload(sec)
    return sec


def test_hash_password_returns_string():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        hashed = sec.hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"


def test_hash_password_is_different_each_time():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        assert sec.hash_password("pass") != sec.hash_password("pass")


def test_verify_password_correct():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        hashed = sec.hash_password("secret123")
        assert sec.verify_password("secret123", hashed) is True


def test_verify_password_incorrect():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        assert sec.verify_password("wrongpass", sec.hash_password("secret123")) is False


def test_create_access_token_returns_string():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        token = sec.create_access_token({"sub": "user-uuid-123"})
        assert isinstance(token, str) and len(token) > 10


def test_create_refresh_token_returns_string():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        assert isinstance(sec.create_refresh_token({"sub": "user-uuid-123"}), str)


def test_decode_token_round_trip():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        token = sec.create_access_token({"sub": "user-uuid-abc"})
        assert sec.decode_token(token)["sub"] == "user-uuid-abc"


def test_decode_invalid_token_raises():
    with patch.dict("os.environ", _SEC_ENV, clear=True):
        sec = _load_security()
        with pytest.raises(Exception):
            sec.decode_token("not.a.valid.token")
