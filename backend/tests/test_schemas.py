import uuid
import pytest
from pydantic import ValidationError


# ── ApiResponse envelope ───────────────────────────────────────────────────
def test_ok_wraps_data():
    from app.schemas.common import ok
    r = ok({"key": "val"})
    assert r.data == {"key": "val"}
    assert r.error is None


def test_err_wraps_error():
    from app.schemas.common import err
    r = err("something failed")
    assert r.data is None
    assert r.error == "something failed"


def test_paginated_meta_defaults():
    from app.schemas.common import PaginatedMeta
    m = PaginatedMeta(total=100)
    assert m.page == 1
    assert m.limit == 20


# ── LoginRequest ───────────────────────────────────────────────────────────
def test_login_request_valid():
    from app.schemas.auth import LoginRequest
    req = LoginRequest(email="user@example.com", password="secret")
    assert req.email == "user@example.com"


def test_login_request_empty_email_rejected():
    from app.schemas.auth import LoginRequest
    with pytest.raises(ValidationError):
        LoginRequest(email="", password="secret")


def test_login_request_empty_password_rejected():
    from app.schemas.auth import LoginRequest
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="")


# ── TokenResponse ──────────────────────────────────────────────────────────
def test_token_response_shape():
    from app.schemas.auth import TokenResponse
    t = TokenResponse(access_token="aaa", refresh_token="bbb")
    assert t.token_type == "bearer"


# ── UserProfileResponse ────────────────────────────────────────────────────
def test_user_profile_response_has_no_password():
    from app.schemas.auth import UserProfileResponse
    uid = uuid.uuid4()
    p = UserProfileResponse(id=uid, email="e@e.com", full_name="Test", role="employee", is_active=True)
    assert not hasattr(p, "hashed_password")
    assert not hasattr(p, "password")


# ── UserCreate ─────────────────────────────────────────────────────────────
def test_user_create_valid():
    from app.schemas.user import UserCreate
    u = UserCreate(email="a@b.com", password="12345678", full_name="Alice", role="employee")
    assert u.email == "a@b.com"


def test_user_create_short_password_rejected():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="short", full_name="Alice", role="employee")


def test_user_create_invalid_email_rejected():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError):
        UserCreate(email="notanemail", password="12345678", full_name="Alice", role="employee")


def test_user_create_invalid_role_rejected():
    from app.schemas.user import UserCreate
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="12345678", full_name="Alice", role="superuser")


# ── UserResponse ───────────────────────────────────────────────────────────
def test_user_response_excludes_hashed_password():
    from app.schemas.user import UserResponse
    uid = uuid.uuid4()
    r = UserResponse(id=uid, email="e@e.com", full_name="Test", role="employee", is_active=True)
    d = r.model_dump()
    assert "hashed_password" not in d
    assert "password" not in d


# ── UserUpdate ─────────────────────────────────────────────────────────────
def test_user_update_all_optional():
    from app.schemas.user import UserUpdate
    u = UserUpdate()  # no fields required
    assert u.email is None


# ── DepartmentCreate ───────────────────────────────────────────────────────
def test_department_create_requires_name():
    from app.schemas.department import DepartmentCreate
    with pytest.raises(ValidationError):
        DepartmentCreate()


def test_department_create_valid():
    from app.schemas.department import DepartmentCreate
    d = DepartmentCreate(name="Engineering")
    assert d.name == "Engineering"
    assert d.parent_id is None


# ── DepartmentResponse ─────────────────────────────────────────────────────
def test_department_response_shape():
    from app.schemas.department import DepartmentResponse
    uid = uuid.uuid4()
    d = DepartmentResponse(id=uid, name="HR")
    assert d.name == "HR"


# ── DocumentCreate: title hardening (CWE-117 log injection) ──────────────────
def test_document_create_strips_control_chars():
    from app.schemas.document import DocumentCreate
    # CR/LF and other control chars must be removed so a crafted title cannot
    # forge or split service log lines.
    d = DocumentCreate(title="Policy\r\nFAKE LOG INJECTED\x00 v2")
    assert "\n" not in d.title
    assert "\r" not in d.title
    assert "\x00" not in d.title
    assert d.title == "PolicyFAKE LOG INJECTED v2"


def test_document_create_rejects_overlong_title():
    from app.schemas.document import DocumentCreate, TITLE_MAX_LENGTH
    with pytest.raises(ValidationError):
        DocumentCreate(title="x" * (TITLE_MAX_LENGTH + 1))


def test_document_create_rejects_empty_after_strip():
    from app.schemas.document import DocumentCreate
    with pytest.raises(ValidationError):
        DocumentCreate(title="\x00\x01\r\n")


def test_document_create_keeps_unicode_and_spaces():
    from app.schemas.document import DocumentCreate
    d = DocumentCreate(title="Политика ИБ 2026")
    assert d.title == "Политика ИБ 2026"
