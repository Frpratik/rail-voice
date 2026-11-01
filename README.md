# RailVoice

Public issue reporting for Indian Railways (Western Railway — Churchgate → Virar).
Passengers report and support station issues; officials triage, assign and escalate them.

| | |
|--|--|
| **Web** | https://rail-voice.vercel.app |
| **API** | https://rail-voice.onrender.com |
| **Docs** | [docs/README.md](docs/README.md) |

## Stack

- **Backend** — FastAPI, async SQLAlchemy, PostgreSQL 16, Alembic (`railvoice-backend/`)
- **Web** — Next.js 16, React 19, Tailwind 4, Zustand, TanStack Query (`railvoice-web/`)
- **Optional** — Redis for rate limiting / idempotency (in-memory fallback in dev)

## Quick start (Docker)

```bash
cp railvoice-backend/.env.example railvoice-backend/.env
docker compose up --build
```

Web: http://localhost:3000 · API: http://localhost:8000 · Docs: http://localhost:8000/docs · Health: `/health/ready`

The seed runs on every start but **only inserts when the database is empty**.
To wipe and reseed: `python -m app.scripts.seed --reset`.

## Local development (no Docker)

```bash
cd railvoice-backend
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload

cd ../railvoice-web
cp .env.local.example .env.local
npm install && npm run dev
```

## Demo accounts (OTP mock mode, code `123456`)

| Persona | Mobile |
|---------|--------|
| Passenger | `+919111111111` |
| Station Admin (Bandra) | `+919888888888` |
| Main Admin | `+919999999999` |

## Features

- **Auth** — mobile OTP, Google (mock or live), refresh-token rotation with reuse detection
- **Issues** — report, list, detail, support (upvote), my issues, comments, photos, text search
- **Duplicate check** — before submitting, passengers see similar open reports at the station and can back one instead
- **Reporter actions** — withdraw until work starts; confirm the fix (closes) or say it isn't fixed (reopens for staff)
- **Moderation** — passengers flag reports and comments; staff review them under Admin → Flagged
- **Staff alerts** — station staff are notified of new, reopened and flagged reports
- **Notifications** — in-app
- **Admin** — dashboard KPIs, location-scoped queue, status transitions, assign, escalate, XLSX/PDF export, user management
- **Help, privacy and terms pages** — public, linked from the footer and sign-in
- **Platform** — daily report limit per person, rate limiting, idempotency keys, Prometheus `/metrics`, correlation IDs

## Project structure

```
railvoice-backend/
├── app/api/v1/      # auth, issues, search, admin, users, social
├── app/core/        # config, security, deps, rate limit, idempotency
├── app/models/      # SQLAlchemy models
├── app/schemas/     # Pydantic DTOs + mappers
├── app/services/    # business logic (issues, auth, users, scope, storage, reports)
├── app/scripts/     # seed
├── alembic/         # migrations
└── tests/
railvoice-web/src/{app,components,lib,providers}
```

## Testing

```bash
cd railvoice-backend
PYTHONPATH=. pytest -v --cov=app
```

Needs PostgreSQL with migrations applied and the seed loaded. See [tests/TEST_PLAN.md](railvoice-backend/tests/TEST_PLAN.md).

## Deployment

- Free demo (Neon + Render + Vercel): [FREE_DEPLOY.md](FREE_DEPLOY.md)
- Self-hosted (Nginx + Docker Compose): [DEPLOY.md](DEPLOY.md)
