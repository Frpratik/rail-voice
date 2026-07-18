# RailVoice

AI-powered public issue reporting for Indian Railways (Western Railway — Churchgate → Virar).

| | |
|--|--|
| **Web** | https://rail-voice.vercel.app |
| **API** | https://rail-voice.onrender.com |
| **Docs (baseline)** | **[docs/README.md](docs/README.md)** — full industry documentation |
| **Repo** | https://github.com/Frpratik/rail-voice |

---

## Backend (implementation)

Production FastAPI backend with PostgreSQL + pgvector, Redis, and Celery.

### Stack

- **FastAPI** — REST API
- **PostgreSQL 16 + pgvector** — relational data + semantic duplicate detection
- **Redis** — cache, rate limits, Celery broker
- **Celery** — background jobs (priority recalc, notifications)

### Quick Start (Docker)

```bash
cp railvoice-backend/.env.example railvoice-backend/.env
docker compose up --build
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs  
Health: http://localhost:8000/health/ready

### Local Development (without Docker)

1. Start PostgreSQL (pgvector) and Redis
2. `cd railvoice-backend`
3. `python -m venv .venv && .venv\Scripts\activate` (Windows)
4. `pip install -r requirements.txt`
5. `cp .env.example .env`
6. `alembic upgrade head`
7. `python -m app.scripts.seed`
8. `uvicorn app.main:app --reload`

### Auth (Development)

OTP mock mode is enabled by default:

```http
POST /api/v1/auth/otp/request
{"mobile": "+919876543210"}

POST /api/v1/auth/otp/verify
{"mobile": "+919876543210", "otp": "123456"}
```

Super Admin seed user: `+919999999999` (login via same OTP flow)

### Core API Flow — Duplicate Detection

```http
POST /api/v1/issues/check-duplicates
{
  "description": "Garbage bins missing beside foot over bridge on Bandra Platform 2",
  "station_id": "<bandra-uuid>"
}

POST /api/v1/issues/{id}/support
# OR

POST /api/v1/issues
{
  "description": "...",
  "station_id": "...",
  "force_create": true,
  "divergence_reason": "Different end of platform"
}
```

### Project Structure

```
railvoice-backend/
├── app/
│   ├── api/v1/          # REST routes
│   ├── ai/              # Embeddings, duplicate detection
│   ├── core/            # Config, auth, enums
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic DTOs
│   ├── services/        # Business logic
│   ├── workers/         # Celery tasks
│   └── scripts/seed.py  # WR corridor seed data
├── alembic/             # Migrations
├── Dockerfile
└── requirements.txt
```

### Embeddings

- With `OPENAI_API_KEY`: uses `text-embedding-3-small` (threshold 0.82)
- Without key: synonym-aware local embedding (threshold 0.48)

### AI Module (`app/ai/`)

| Component | Purpose |
|-----------|---------|
| `embeddings.py` | OpenAI + local fallback |
| `duplicate.py` | Semantic duplicate detection |
| `categorizer.py` | Issue category + confidence |
| `severity.py` | Severity 1–5 prediction |
| `spam.py` | Spam/fake auto-hold |
| `priority_predictor.py` | AI priority score |
| `search.py` | Hybrid semantic + keyword (RRF) |
| `trending.py` | Trending velocity score |
| `summarizer.py` | Issue summaries |
| `daily_summary.py` | Admin daily narrative |
| `image_validator.py` | Photo validation |
| `pipeline.py` | Orchestrates all on create |

### AI API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/search?q=` | Hybrid search |
| `POST /api/v1/search/semantic` | Semantic search |
| `GET /api/v1/admin/analytics/ai-insights/daily-summary` | Daily AI summary |
| `GET /api/v1/admin/spam-queue` | Spam review queue |

### Implemented Endpoints (MVP)

| Module | Endpoints |
|--------|-----------|
| Auth | OTP, anonymous session, logout |
| Stations | List, get by code |
| Issues | Create, check duplicates, list, detail, support |
| Admin | Dashboard, queue, status update |

### Next Phase

Phase 8: Next.js frontend — see `railvoice-web/`

---

## Frontend (Phase 8)

```bash
cd railvoice-web
cp .env.local.example .env.local
npm install
npm run dev
```

Web: http://localhost:3000  
Requires API at http://localhost:8000

### Frontend screens

| Screen | Route |
|--------|-------|
| Home feed | `/` |
| Report + duplicate detection | `/report` |
| Issue detail + timeline | `/issues/[id]` |
| Station issues | `/stations/[code]` |
| Login (OTP) | `/login` |
| Profile | `/profile` |
| Admin dashboard | `/admin/dashboard` |
| Admin issue queue | `/admin/issues` |

## Testing (Phase 10)

```bash
cd railvoice-backend
PYTHONPATH=. pytest -v --cov=app
```

See [tests/TEST_PLAN.md](railvoice-backend/tests/TEST_PLAN.md) for full strategy.

| Suite | Tests |
|-------|-------|
| Unit (AI) | `test_ai.py`, `test_ai_eval.py` |
| Integration | `test_api.py`, `test_auth.py`, `test_admin.py`, `test_search.py`, `test_security.py` |
| Load (k6) | `tests/load/smoke.js` |

CI runs backend tests with **≥55% coverage** + frontend build/lint.

## Deployment (Phase 11)

### Free demo (recommended if you have no VPS)

Use **Neon + Render + Vercel** — $0. See **[FREE_DEPLOY.md](FREE_DEPLOY.md)**.

### Self-hosted / VPS

Production stack: Nginx + Next.js + Gunicorn API + Celery + Postgres/pgvector + Redis.

Full runbook: **[DEPLOY.md](DEPLOY.md)**

```bash
cp .env.production.example .env.production
# edit secrets, domains, CORS
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

| Surface | URL |
|---------|-----|
| App (via Nginx) | `http://YOUR_HOST/` |
| API health | `http://YOUR_HOST/health` |
| API docs | `http://YOUR_HOST/docs` |

Local daily development still uses `docker compose up` (ports 3000 / 8000).
