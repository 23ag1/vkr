# Implementation Plan — Phase 1: Infrastructure

Generated: 2026-05-12 | TDD-first order | Beads: vkr-d8g, vkr-xc2, vkr-xm3, vkr-3f7, vkr-rvb

## Gap Analysis

**Exists:** CLAUDE.md, .env.example, .gitignore, backend/.flake8, backend/pyproject.toml,
frontend/.eslintrc.json, frontend/.prettierrc

**Missing:** everything else — all source files, docker, migrations, tests.

---

## Task List (dependency order, TDD-first)

### 1.1 — Directory Scaffold (vkr-d8g)
- [ ] T01 — Create backend/app/ package tree (models/, schemas/, routers/, services/, core/)
- [ ] T02 — Create backend/tests/ with conftest.py stub
- [ ] T03 — Create frontend/src/ directory tree (api/, store/, hooks/, components/, pages/)
- [ ] T04 — Copy .env.example → .env (dev defaults, no real secrets needed yet)

### 1.2 — Docker Compose (vkr-xc2)
- [ ] T05 — Write docker-compose.yml: postgres (pgvector/pgvector:pg16), backend, frontend
- [ ] T06 — Write backend/Dockerfile (python:3.11-slim, uvicorn, hot-reload)
- [ ] T07 — Write frontend/Dockerfile (node:20-alpine, vite dev server)
- [ ] T08 — Verify `docker-compose config` parses without errors

### 1.3 — Backend Boilerplate (vkr-xm3)
- [ ] T09  — Write backend/requirements.txt (pinned versions)
- [ ] T10 — [RED]  Write tests/test_config.py — test Settings loads, DATABASE_URL built correctly
- [ ] T11 — [GREEN] Write app/config.py — Pydantic Settings, DATABASE_URL property, validation
- [ ] T12 — [RED]  Write tests/test_database.py — test engine created, session factory exists
- [ ] T13 — [GREEN] Write app/database.py — async engine, AsyncSessionLocal, get_db dep
- [ ] T14 — Write app/main.py — FastAPI factory, CORS, lifespan, include routers stub
- [ ] T15 — Write app/deps.py — get_db, get_current_user stub (implemented in Phase 2)

### 1.4 — SQLAlchemy Models + Alembic (vkr-3f7)
- [ ] T16 — Write app/models/base.py — DeclarativeBase, UUIDMixin, TimestampMixin
- [ ] T17 — Write app/models/department.py — Department (self-ref FK)
- [ ] T18 — Write app/models/user.py — User (role VARCHAR, dept FK)
- [ ] T19 — Write app/models/module.py — Module (ARRAY target_roles, topic VARCHAR)
- [ ] T20 — Write app/models/learning.py — LearningPath (UniqueConstraint user+module)
- [ ] T21 — Write app/models/test.py — Question, UserAnswer
- [ ] T22 — Write app/models/chat.py — ChatSession, ChatMessage (sources JSON)
- [ ] T23 — Write app/models/rag.py — Document, DocumentChunk (Vector(1536))
- [ ] T24 — Write app/models/phishing.py — PhishingTemplate, PhishingCampaign, PhishingRecipient
- [ ] T25 — Write app/models/audit.py — AuditLog (immutable, no updated_at)
- [ ] T26 — Write app/models/__init__.py — re-export all models for Alembic discovery
- [ ] T27 — Write alembic.ini + alembic/env.py (async-aware, reads DATABASE_URL from env)
- [ ] T28 — [VERIFY] Run `alembic revision --autogenerate` → inspect generated migration
- [ ] T29 — [VERIFY] Run `alembic upgrade head` inside Docker → 0 errors, all tables created

### 1.5 — Core Security (vkr-rvb)
- [ ] T30 — [RED]  Write tests/test_security.py (7 tests: hash, verify ×2, create token, decode, expired, invalid)
- [ ] T31 — [GREEN] Write app/core/security.py — hash_password, verify_password, create_access_token, create_refresh_token, decode_token
- [ ] T32 — Write app/core/exceptions.py — CredentialsException, ForbiddenException, NotFoundException
- [ ] T33 — [VERIFY] `pytest tests/ -v --tb=short` → all green

---

## Verification Gates

After ALL tasks:
1. `docker-compose up --build` → all 3 services start (no crash-loops)
2. `curl http://localhost:8000/health` → `{"status": "ok"}`
3. `docker-compose exec backend alembic upgrade head` → 14 tables created in postgres
4. `docker-compose exec backend pytest tests/ -v` → all tests pass
5. `curl http://localhost:5173` → Vite dev server responds

---

## Notes
- pgvector column in document_chunks uses `pgvector.sqlalchemy.Vector` type
- Alembic env.py must use `run_async_migrations()` pattern for asyncpg
- ARRAY type for `target_roles` uses `sqlalchemy.ARRAY(sqlalchemy.String)`
- All enum values stored as VARCHAR — no Postgres ENUM type
- Tests use `pytest-asyncio` in asyncio_mode = "auto"
