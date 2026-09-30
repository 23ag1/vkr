# VKR — Security Awareness Platform

Graduation thesis prototype: a web application that trains employees in information
security and measures how well the training sticks.

- **Adaptive testing** — an LLM writes questions from the module content and explains wrong answers.
- **AI mentor** — answers from the organisation's own documents (RAG over pgvector).
- **Simulated phishing** — campaigns with tracking, so behaviour is checked in practice, not only in tests.
- **Analytics** — per-person and per-department picture of where the weak spots are.
- Built around Russian requirements: 152-FZ, 187-FZ, FSTEC Order No. 21.

## Stack

FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL 16 + pgvector · React 18 · TypeScript ·
Vite · Tailwind · TanStack Query · OpenAI (GPT-4o, text-embedding-3-small) · Docker Compose

## Run

```bash
cp .env.example .env        # fill in OPENAI_API_KEY, SECRET_KEY, DB password
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed   # prints demo passwords unless SEED_*_PASSWORD are set
```

Frontend: http://localhost:5173 · API: http://localhost:8000/docs

Demo users: `admin@`, `specialist@`, `manager@`, `employee@vkr.example.com`.
