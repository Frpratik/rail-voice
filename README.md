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
| `visual_verifier.py` | 64-bit dHash perceptual visual verification & duplicate image detection |
| `sla_predictor.py` | AI SLA velocity risk engine & predictive escalation radar |
| `voice_assistant.py` | Multilingual vernacular voice parser (Hindi, Marathi, Gujarati, Hinglish, English) |
| `pipeline.py` | Orchestrates all on create |

### Production Innovation Features & API Endpoints

| Feature | Module / Endpoint | Description |
|---------|-------------------|-------------|
| **AI Vernacular Voice Assistant** | `POST /api/v1/voice/parse`<br>`POST /api/v1/voice/create-issue` | Spoken grievance parsing in Hindi, Marathi, Gujarati, Hinglish & English with station extraction |
| **Predictive SLA Risk Radar** | `GET /api/v1/admin/sla-risk-radar` | Real-time predictive SLA breach velocity forecasting & escalation queue |
| **WhatsApp Conversational Bot** | `POST /api/v1/whatsapp/webhook`<br>`POST /api/v1/whatsapp/simulate` | WhatsApp native multi-turn reporting bot & webhook simulation |
| **Visual Verification & Tamper Detection** | `app/ai/visual_verifier.py` | 64-bit dHash image authentication & duplicate photo fraud prevention |
| **Emergency Safety Alert Network** | `GET /api/v1/emergency/alerts`<br>`POST /api/v1/emergency/alerts` | Real-time emergency hazard broadcasts for active commuters |
| **Leaderboard & Gamification** | `GET /api/v1/gamification/leaderboard/users`<br>`GET /api/v1/gamification/reputation/me` | Civic karma points, badges, user & station community leaderboards |
| **Command Center Command K** | `src/components/admin/command-palette.tsx` | Instant keyboard-driven Command+K palette across operations |

### Implemented Endpoints

| Module | Endpoints |
|--------|-----------|
| Auth | OTP, anonymous session, Google OAuth (mock/live), logout |
| Stations | List, get by code |
| Issues | Create, check duplicates, list, detail, support |
| Voice | Parse vernacular transcript, create voice issue |
| WhatsApp | Inbound webhook, outbound reply, simulate |
| Emergency | List active alerts, create alert, deactivate alert |
| Gamification | User leaderboard, station leaderboard, my reputation |
| Admin | Dashboard, queue, status update, SLA risk radar |

---

## Frontend (Phase 8 & Production Features)

```bash
cd railvoice-web
cp .env.local.example .env.local
npm install
npm run dev
```

Web: http://localhost:3000  
Requires API at http://localhost:8000

### Frontend screens & components

| Screen / Component | Route / Component | Description |
|--------------------|-------------------|-------------|
| Home feed | `/` | Live issue feed & search |
| Report + Voice AI | `/report` | Interactive 3-step report + AI Vernacular Voice Assistant modal |
| Leaderboard | `/leaderboard` | User & station community rankings |
| Issue detail | `/issues/[id]` | Detail, timeline, visual AI authentication badge |
| Station issues | `/stations/[code]` | Station-scoped grievance queue |
| Login (OTP/Google) | `/login` | Mobile OTP & Google single sign-on |
| Profile & Rep | `/profile` | User settings + Karma Points & Badge card |
| Admin dashboard | `/admin/dashboard` | KPIs, SLA Risk Radar, WhatsApp Simulator, Emergency Broadcast modal |
| Admin issue queue | `/admin/issues` | Operations triage queue |
| Command Palette | `Cmd+K` | Quick navigation across operations |

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
