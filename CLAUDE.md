# VKR — Web Application for Employee Information Security Awareness

## Project Overview

Diploma thesis prototype: a web application for training and assessing employees
on information security awareness. Integrates an LLM (GPT-4o) for adaptive
testing, a RAG-based AI mentor, simulated phishing campaigns, and analytics.

Complies with Russian regulations: ФЗ-152, ФЗ-187, Приказ ФСТЭК №21.

---

## Stack

| Layer      | Technology                                        |
|------------|---------------------------------------------------|
| Backend    | Python 3.11 · FastAPI · SQLAlchemy 2 async · Alembic |
| Frontend   | React 18 · TypeScript · Vite · Tailwind CSS       |
| State      | Zustand (auth) · TanStack Query (server state)    |
| Database   | PostgreSQL 16 + pgvector extension                |
| LLM        | OpenAI GPT-4o (completions) · text-embedding-3-small (RAG) |
| Deploy     | Docker · docker-compose                           |
| Auth       | JWT access + refresh tokens · bcrypt              |

---

## Repository Layout

```
vkr/
├── CLAUDE.md
├── AGENTS.md
├── ARCHITECTURE.md
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py          # FastAPI app factory
│       ├── config.py        # Pydantic Settings
│       ├── database.py      # Async engine + session
│       ├── deps.py          # FastAPI dependencies (get_db, current_user)
│       ├── core/
│       │   ├── security.py  # JWT, bcrypt
│       │   └── exceptions.py
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic request/response schemas
│       ├── routers/         # FastAPI routers (thin — no business logic)
│       └── services/        # Business logic layer
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── api/             # axios functions per domain
        ├── store/           # Zustand stores
        ├── hooks/           # Custom React hooks
        ├── components/
        │   ├── layout/      # Sidebar, Header, Layout
        │   └── ui/          # Button, Card, Badge, Modal, Progress
        └── pages/
            ├── auth/
            ├── employee/
            └── admin/
```

---

## Architecture Rules

### Backend

1. **Routers are thin** — only HTTP concerns (parse request, call service, return response).
   No SQL, no business logic in routers.
2. **Services own logic** — all domain rules, LLM calls, DB operations live in `services/`.
3. **Deps via FastAPI Depends** — `get_db`, `get_current_user`, `require_role(...)`.
4. **Schemas ≠ Models** — always separate Pydantic schemas from SQLAlchemy models.
5. **Async everywhere** — all DB access uses `async with session`, all I/O is awaited.
6. **Immutability** — never mutate ORM objects in-place; build new instances or use
   `model_copy()` on Pydantic. Return new dicts instead of modifying existing ones.

### Frontend

1. **Pages are thin** — pages compose components, delegate data fetching to hooks.
2. **TanStack Query for server state** — no manual `useEffect` + `fetch` for API calls.
3. **Zustand only for client state** — auth token, user profile, UI flags.
4. **No inline styles, no `!important`** — Tailwind utility classes only.
5. **Components < 300 lines** — split if larger.
6. **TypeScript strict** — no `any`, no `@ts-ignore`.

---

## API Contract

### Response Envelope

Every endpoint returns:

```json
{
  "data": <payload | null>,
  "error": <string | null>,
  "meta": { "total": 0, "page": 1, "limit": 20 }   // pagination only
}
```

### HTTP Status Codes

| Situation            | Code |
|----------------------|------|
| Success (GET/PUT)    | 200  |
| Created (POST)       | 201  |
| Bad request / validation | 422 |
| Unauthorized         | 401  |
| Forbidden (wrong role) | 403 |
| Not found            | 404  |
| Server error         | 500  |

### Auth

All protected routes require `Authorization: Bearer <access_token>`.
Access token TTL: 30 min. Refresh token TTL: 7 days.

---

## Database Conventions

- All PKs are `UUID` generated server-side (`uuid4`).
- All tables have `created_at TIMESTAMPTZ DEFAULT now()`.
- Mutable tables also have `updated_at TIMESTAMPTZ`.
- Foreign keys always have explicit `ondelete` behavior.
- Enum values stored as `VARCHAR` with a CHECK constraint (not Postgres ENUM type)
  so Alembic migrations stay simple.
- Vector columns: `VECTOR(1536)` for `text-embedding-3-small`.
- Never `SELECT *` — always name columns explicitly in queries.

### Tables (summary)

| Table                | Purpose                                      |
|----------------------|----------------------------------------------|
| `users`              | Accounts with role + department              |
| `departments`        | Org hierarchy (self-referencing)             |
| `modules`            | Learning content units                       |
| `learning_paths`     | Per-user module assignment + progress        |
| `questions`          | LLM-generated questions (stored for audit)  |
| `user_answers`       | Employee answers + is_correct                |
| `chat_sessions`      | Mentor conversation sessions                 |
| `chat_messages`      | Individual messages + sources JSON           |
| `documents`          | RAG source documents                         |
| `document_chunks`    | Chunked text + embedding vector              |
| `phishing_templates` | Email template library                       |
| `phishing_campaigns` | Campaign instances                           |
| `phishing_recipients`| Per-user tracking (opened/clicked/reported)  |
| `audit_logs`         | Immutable event journal                      |

---

## Roles & Permissions

| Role                 | Key Permissions                                        |
|----------------------|--------------------------------------------------------|
| `employee`           | View own modules, take tests, use mentor, view own progress |
| `admin`              | Full module/user/campaign management, analytics        |
| `security_specialist`| Read audit logs, risk profiles, all phishing results  |
| `manager`            | Read aggregated department analytics                   |

---

## LLM Integration Standards

- **Structured output** — always use `response_format={"type": "json_object"}` or
  Pydantic model parsing. Never parse free-form text.
- **System prompts** — stored as constants in `services/prompts.py`, not inline strings.
- **Retry** — wrap OpenAI calls with `tenacity` (3 attempts, exponential backoff).
- **Validation** — validate LLM JSON response against Pydantic schema before persisting.
- **Logging** — every LLM call logs: user_id, tokens_used, latency_ms, scenario.
- **RAG context limit** — inject max 5 chunks, each ≤ 500 tokens, into the prompt.
- **Never** send PII (full names, emails) to the LLM.

---

## Quality Standards

### Code Size Limits

| Unit         | Max lines |
|--------------|-----------|
| Function     | 50        |
| Router file  | 150       |
| Service file | 400       |
| Component    | 300       |
| Any file     | 500       |

### Performance Targets

| Operation                  | Target     |
|----------------------------|------------|
| API response (non-LLM)     | < 200 ms   |
| LLM question generation    | < 8 s      |
| LLM mentor response        | < 15 s     |
| Vector similarity search   | < 100 ms   |
| Page initial load          | < 2 s      |

### Security Checklist (before each commit)

- [ ] No secrets in code (use `.env`)
- [ ] All user input validated via Pydantic schema
- [ ] Role check on every protected endpoint
- [ ] No raw SQL string concatenation — use SQLAlchemy ORM or bound params
- [ ] Audit log written for: login, module complete, test submit, phishing action
- [ ] LLM input sanitized (strip prompt injection patterns)
- [ ] Phishing tracking page does NOT store actual credentials

---

## Key Metrics (aligned with thesis section 3.1)

### Coverage metrics (базовый уровень зрелости)
- % employees who completed mandatory modules on time
- % of test sessions with passing score (≥ 70%)

### Behavioral metrics (уровень осведомлённости)
- Phishing click rate per campaign
- Phishing report rate per campaign
- Mentor session count per employee per month

### Integrity metrics (уровень устойчивости)
- Avg test score delta (first attempt vs latest)
- Time-to-complete per module (shows engagement quality)

All metrics available via `/api/analytics/*` endpoints.
Audit log provides documentary evidence for ФСТЭК №21 compliance checks.

---

## Dev Workflow

### Running locally (full stack)

```bash
cp .env.example .env          # fill OPENAI_API_KEY
docker-compose up --build     # starts postgres, backend, frontend
# backend:  http://localhost:8000  (Swagger at /docs)
# frontend: http://localhost:5173
```

### Backend only

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Database migrations

```bash
# inside backend container or venv:
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### Seed demo data

```bash
docker-compose exec backend python -m app.seed
```

### Beads workflow

```bash
bd ready                      # find next task
bd update <id> --claim        # claim before starting
bd close <id>                 # close when done
```

---

## Architecture: Data Flows

### AI Testing (Scenarios 1 & 2)

```
Employee → POST /api/testing/generate
  service: load module text from DB
           build system prompt + module content
           call GPT-4o → validate via QuestionSchema (Pydantic)
           persist Question (for audit)
           return question + options

Employee submits → POST /api/testing/answer
  service: compare to correct_answer
           if wrong → call GPT-4o for explanation (with RAG context)
           persist UserAnswer
           write audit_log entry
           return {is_correct, explanation, correct_answer}
```

### RAG Mentor (Scenario 3)

```
Admin uploads doc → POST /api/documents/upload
  service: extract text → split chunks (≤500 tokens, 50 overlap)
           per chunk: text-embedding-3-small → vector[1536]
           persist DocumentChunk rows

Employee sends message → POST /api/mentor/sessions/{id}/messages
  service: embed query → cosine search (pgvector <=>)  → top-5 chunks
           build prompt: system + chunks + last-10 messages
           call GPT-4o → stream response
           persist ChatMessage + sources JSON
```

### Phishing (in-app simulation)

```
Admin launches campaign → creates PhishingRecipient per user with UUID token

Employee sees email in notification feed
  → GET /phishing/track/{token}/open       → sets opened_at
  → GET /phishing/track/{token}/click      → sets clicked_at, redirects to landing
  → POST /phishing/track/{token}/submit    → sets submitted_at (NO credential storage)
  → POST /api/phishing/report/{token}      → sets reported_at (positive action)
```

## Architecture: Routing Map

```
# Public
GET  /phishing/landing/:token           Simulated credential page

# Auth
POST /api/auth/login
POST /api/auth/refresh
GET  /api/auth/me

# Users (admin)
GET|POST          /api/users
GET|PUT|DELETE    /api/users/{id}

# Departments (admin)
GET|POST          /api/departments
GET|PUT|DELETE    /api/departments/{id}

# Modules
GET               /api/modules              (all roles, filtered by role)
POST              /api/modules              (admin)
GET|PUT|DELETE    /api/modules/{id}         (admin write, all read)
POST              /api/modules/{id}/publish (admin)

# Learning paths
GET    /api/learning/my                    employee's own path
POST   /api/learning/assign               admin assigns module to users
PATCH  /api/learning/{id}/progress        employee updates progress

# Testing
POST   /api/testing/generate              generate question for module
POST   /api/testing/answer               submit answer, get feedback
GET    /api/testing/history              employee's test history

# Mentor (RAG chat)
GET|POST          /api/mentor/sessions
GET               /api/mentor/sessions/{id}/messages
POST              /api/mentor/sessions/{id}/messages

# Documents (RAG source)
GET               /api/documents          (admin, security_specialist)
POST              /api/documents/upload   (admin)
DELETE            /api/documents/{id}     (admin)

# Phishing
GET|POST          /api/phishing/templates
GET|PUT|DELETE    /api/phishing/templates/{id}
GET|POST          /api/phishing/campaigns
POST              /api/phishing/campaigns/{id}/launch
POST              /api/phishing/campaigns/{id}/complete
GET               /api/phishing/campaigns/{id}/results
POST              /api/phishing/report/{token}

# Analytics
GET  /api/analytics/overview             org-level summary (admin, manager)
GET  /api/analytics/departments          per-dept breakdown
GET  /api/analytics/users/{id}           individual profile
GET  /api/analytics/phishing/{campaign}  campaign metrics

# Audit log
GET  /api/audit                          (security_specialist, admin)
```

---

## Dev Notes

### External dependencies

- **openai** — LLM completions + embeddings (text-embedding-3-small, 1536 dims)
- **pgvector** — Postgres extension + `pgvector` Python library for vector ops
- **python-jose** — JWT encode/decode
- **passlib[bcrypt]** — password hashing
- **tenacity** — retry logic for OpenAI calls
- **python-multipart** — file upload support (document ingestion)

### Known constraints

- Phishing campaigns do NOT send real emails — recipients see campaigns in the
  notification feed inside the app. Click/submit tracking uses unique tokens via
  in-app links.
- LLM question generation is synchronous per request (no queue). Acceptable for
  prototype; production would use a task queue (Celery/ARQ).
- pgvector cosine similarity search uses `<=>` operator. Index: `ivfflat`.
- All dates stored as UTC; frontend localizes for display.
