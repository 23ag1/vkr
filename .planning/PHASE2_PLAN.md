# Implementation Plan — Phase 2: Auth & Users

Generated: 2026-05-12 | TDD-first | Stack: FastAPI + SQLAlchemy 2 async + JWT + bcrypt

---

## Gap Analysis

### Exists (Phase 1 output)
- `app/core/security.py` — hash_password, verify_password, create_access_token, create_refresh_token, decode_token
- `app/core/exceptions.py` — CredentialsException, ForbiddenException, NotFoundException
- `app/deps.py` — get_db ✓, get_current_user STUB (raises 501), get_current_admin STUB
- `app/models/user.py` — User (email, hashed_password, full_name, role, is_active, department_id)
- `app/models/department.py` — Department (name, parent_id self-ref)
- `app/models/audit.py` — AuditLog (user_id, action, details, ip_address)
- `app/main.py` — FastAPI app, CORS, /health (no routers registered yet)

### Missing (Phase 2 deliverables)
- `app/schemas/` — empty; need common envelope + auth/user/dept schemas
- `app/services/` — empty; need auth, user, department service modules
- `app/routers/` — empty; need auth, users, departments router modules
- `app/deps.py` — get_current_user stub must be implemented
- `app/main.py` — routers must be registered

---

## Architecture Decisions

### API Envelope (CLAUDE.md)
Every response: `{"data": <payload|null>, "error": <string|null>}`
Paginated: add `"meta": {"total": N, "page": P, "limit": L}`

### Roles (CLAUDE.md Roles table)
`employee` | `admin` | `security_specialist` | `manager`

### Auth Flow
1. `POST /api/auth/login` → verify email+password → return {access_token, refresh_token}
2. `POST /api/auth/refresh` → verify refresh token → return new access_token
3. `GET /api/auth/me` → decode Bearer → return UserProfileResponse

### JWT Payload
`{"sub": str(user.id), "role": user.role, "exp": ...}`

### User soft-delete
`DELETE /api/users/{id}` sets `is_active=False` — never hard-deletes.

### Testing strategy
- Schema tests: pure unit (no DB)
- Service tests: unit with mocked AsyncSession (unittest.mock.AsyncMock)
- Router tests: FastAPI TestClient + dependency_overrides to inject mock services
- All async tests need `@pytest.mark.anyio`

---

## Task List (TDD-first, dependency order)

### 2.1 — Schemas (no DB, pure unit)

- [ ] T01 — [RED] Write `tests/test_schemas.py` — validate LoginRequest rejects empty fields,
      TokenResponse shape, UserCreate enforces password min-length, UserResponse excludes
      hashed_password, DepartmentCreate requires name, ApiResponse envelope wraps data/error
- [ ] T02 — [GREEN] Write `app/schemas/common.py` — `ApiResponse[T]` generic, `PaginatedMeta`,
      `paginated_response()` helper, `ok()` / `err()` factory functions
- [ ] T03 — [GREEN] Write `app/schemas/auth.py` — `LoginRequest`, `TokenResponse`,
      `UserProfileResponse` (id, email, full_name, role, department_id)
- [ ] T04 — [GREEN] Write `app/schemas/user.py` — `UserCreate` (email, password min-8,
      full_name, role, department_id?), `UserUpdate` (all optional), `UserResponse`
      (never exposes hashed_password)
- [ ] T05 — [GREEN] Write `app/schemas/department.py` — `DepartmentCreate` (name, parent_id?),
      `DepartmentUpdate` (all optional), `DepartmentResponse`

### 2.2 — Deps wiring

- [ ] T06 — [RED] Write `tests/test_deps_auth.py` — test get_current_user: valid JWT returns user dict,
      missing Bearer raises 401, invalid token raises 401, inactive user raises 401
- [ ] T07 — [GREEN] Update `app/deps.py` — implement get_current_user (decode JWT → SELECT user →
      check is_active → return User ORM obj); add `require_role(*roles)` Depends factory
      that raises 403 if user.role not in roles

### 2.3 — Auth Service

- [ ] T08 — [RED] Write `tests/test_service_auth.py` — test authenticate_user returns User on correct
      credentials, returns None on wrong password, returns None on unknown email;
      test build_token_pair returns dict with access_token + refresh_token
- [ ] T09 — [GREEN] Write `app/services/auth.py` — `authenticate_user(db, email, password) -> User|None`,
      `build_token_pair(user) -> dict`, `get_user_from_token(db, token) -> User|None`

### 2.4 — User Service

- [ ] T10 — [RED] Write `tests/test_service_user.py` — test list_users returns list, test get_user
      returns User or raises 404, test create_user hashes password and persists, test
      update_user applies partial changes, test deactivate_user sets is_active=False
- [ ] T11 — [GREEN] Write `app/services/user.py` — `list_users(db, skip, limit)`,
      `get_user(db, user_id)`, `create_user(db, data: UserCreate)`,
      `update_user(db, user_id, data: UserUpdate)`, `deactivate_user(db, user_id)`

### 2.5 — Department Service

- [ ] T12 — [RED] Write `tests/test_service_department.py` — test list_departments, get_department,
      create_department, update_department, delete_department
- [ ] T13 — [GREEN] Write `app/services/department.py` — `list_departments(db)`,
      `get_department(db, dept_id)`, `create_department(db, data)`,
      `update_department(db, dept_id, data)`, `delete_department(db, dept_id)`

### 2.6 — Auth Router (integration)

- [ ] T14 — [RED] Write `tests/test_router_auth.py` — POST /api/auth/login 200 on valid creds,
      POST /api/auth/login 401 on wrong password, POST /api/auth/refresh 200 on valid token,
      GET /api/auth/me 200 returns profile, GET /api/auth/me 401 without token
- [ ] T15 — [GREEN] Write `app/routers/auth.py` — POST /login (call auth_service.authenticate_user,
      write AuditLog, return tokens), POST /refresh (decode refresh token, issue new access),
      GET /me (Depends get_current_user, return UserProfileResponse)
- [ ] T16 — [GREEN] Update `app/main.py` — include auth router at prefix `/api/auth`

### 2.7 — Users Router (integration)

- [ ] T17 — [RED] Write `tests/test_router_users.py` — GET /api/users 200 (admin), GET /api/users
      403 (employee), POST /api/users 201 creates user, GET /api/users/{id} 200,
      GET /api/users/{id} 404 on unknown id, PUT /api/users/{id} 200 updates,
      DELETE /api/users/{id} 200 deactivates
- [ ] T18 — [GREEN] Write `app/routers/users.py` — thin router calls user_service,
      admin-only via require_role("admin"), returns ApiResponse envelope
- [ ] T19 — [GREEN] Update `app/main.py` — include users router at prefix `/api/users`

### 2.8 — Departments Router (integration)

- [ ] T20 — [RED] Write `tests/test_router_departments.py` — GET /api/departments 200,
      POST /api/departments 201, GET /api/departments/{id} 200/404,
      PUT /api/departments/{id} 200, DELETE /api/departments/{id} 200
- [ ] T21 — [GREEN] Write `app/routers/departments.py` — thin router, admin-only
- [ ] T22 — [GREEN] Update `app/main.py` — include departments router

### 2.9 — Verify

- [ ] T23 — [VERIFY] `pytest tests/ -v --tb=short` — all tests pass (Phase 1 + Phase 2)
- [ ] T24 — [VERIFY] Manual smoke: POST /api/auth/login with seed user returns tokens

---

## File Creation Map

```
app/
  schemas/
    __init__.py
    common.py          # ApiResponse[T], PaginatedMeta, ok(), err()
    auth.py            # LoginRequest, TokenResponse, UserProfileResponse
    user.py            # UserCreate, UserUpdate, UserResponse
    department.py      # DepartmentCreate, DepartmentUpdate, DepartmentResponse
  services/
    __init__.py
    auth.py            # authenticate_user, build_token_pair, get_user_from_token
    user.py            # list_users, get_user, create_user, update_user, deactivate_user
    department.py      # list_departments, get_department, create/update/delete_department
  routers/
    __init__.py
    auth.py            # /login /refresh /me
    users.py           # / /{id}
    departments.py     # / /{id}
tests/
  test_schemas.py
  test_deps_auth.py
  test_service_auth.py
  test_service_user.py
  test_service_department.py
  test_router_auth.py
  test_router_users.py
  test_router_departments.py
```

---

## Security Constraints (from CLAUDE.md)

- Audit log written on every login
- Role check on every protected endpoint
- No secrets in code
- All user input validated via Pydantic schema
- Password never returned in any response

---

## Notes

- `asyncio_mode = STRICT` in current pytest config — all async tests need `@pytest.mark.anyio`
- Router tests use `dependency_overrides` to inject mock services — no real DB needed
- Service tests use `AsyncMock` for the session object
- `require_role` returns a `Depends`-compatible callable checking `current_user.role`
- Refresh token flow: decode token → check `token_type == "refresh"` claim → issue new access token
- `token_type` claim added to JWT payload to distinguish access vs refresh tokens
