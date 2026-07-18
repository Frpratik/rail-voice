# 2. System Architecture

## 2.1 High-level diagram

```
┌─────────────────────┐         ┌──────────────────────────┐
│  Browser            │         │  Vercel (Next.js)        │
│  rail-voice.vercel  │────────▶│  UI + /api/* rewrite     │
└─────────────────────┘         └────────────┬─────────────┘
                                             │ proxy
                                             ▼
                                ┌──────────────────────────┐
                                │  Render (FastAPI)        │
                                │  rail-voice.onrender.com │
                                │  Gunicorn / Uvicorn      │
                                └───────┬──────────┬───────┘
                                        │          │
                         ┌──────────────┘          └──────────────┐
                         ▼                                        ▼
              ┌─────────────────────┐                 ┌──────────────────┐
              │ Neon Postgres       │                 │ Local media vol  │
              │ + pgvector          │                 │ (ephemeral free) │
              └─────────────────────┘                 └──────────────────┘
```

Local/dev adds **Redis + Celery worker + beat**. Free production runs with `CELERY_ENABLED=false` (in-process / sync AI on create).

## 2.2 Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| Web | Next.js 16, React 19, Tailwind 4, Zustand, TanStack Query | Passenger + admin UI |
| API | FastAPI, SQLAlchemy async, Pydantic | REST, auth, business rules |
| DB | PostgreSQL 16 + pgvector (Neon free / Docker local) | Persistence + embeddings |
| Cache / queue | Redis + Celery (optional) | Background scoring, notifications |
| Storage | Local filesystem (`/media`) | Issue photos |
| Edge (VPS) | Nginx | TLS, reverse proxy, rate zones |
| Observability | Prometheus `/metrics`, correlation IDs | Ops |

## 2.3 Request flow — report an issue

```
User → /report (Next.js)
  → ensure anonymous or JWT
  → POST /issues/check-duplicates
       → embed description → station-scoped similarity search
  → if similar: DuplicateSheet (support OR force_create + divergence_reason)
  → POST /issues
       → AI pipeline (embed, category, severity, spam, priority, summary)
       → timeline SUBMITTED
  → optional POST /issues/{id}/photos
  → redirect /issues/{id}
```

## 2.4 Request flow — official triage

```
Official (JWT + role) → /admin/issues
  → GET /admin/issues
  → PATCH status | POST assign | POST escalate
  → Notification rows for creator / assignee
  → Timeline events (status_change / ASSIGNED / ESCALATED)
```

## 2.5 Same-origin API proxy (production web)

Vercel does **not** call Render cross-origin from the browser for API calls in production default:

- Browser calls `https://rail-voice.vercel.app/api/v1/...`
- `next.config.ts` rewrites `/api/*` → `https://rail-voice.onrender.com/api/*`
- Avoids baked `localhost` and reduces CORS friction

`NEXT_PUBLIC_API_URL` may be `/api/v1` (prod) or `http://localhost:8000/api/v1` (local).

## 2.6 Environments

| Env | App config | Auth | Infra |
|-----|------------|------|-------|
| Local Docker | `DEBUG=true`, mock OTP | Mock | Compose: Postgres, Redis, API, worker, beat |
| Staging / free prod | `APP_ENV=staging` | Mock OTP/Google allowed | Neon + Render + Vercel |
| Hardened production | `APP_ENV=production` | Mocks **blocked** at startup | VPS compose or cloud with real secrets |

## 2.7 Design principles

1. **Envelope responses** — `{ data, meta }` for JSON APIs  
2. **Reporter identity abstraction** — JWT or anonymous session for writes  
3. **AI on create path** — sync analysis so free tier works without workers  
4. **Official gate** — single `require_official` for admin surface  
5. **Audit timeline** — status/assignment/escalation/comments leave trails  

## 2.8 Key packages (backend)

FastAPI, SQLAlchemy asyncio, asyncpg, Alembic, pgvector, python-jose, Celery, Redis, OpenAI (optional), openpyxl, reportlab, google-auth, Pillow, prometheus-client, bleach.

## 2.9 Key packages (frontend)

Next.js, React, TanStack Query, Zustand, Framer Motion, Lucide, Sonner, Tailwind CSS 4, Zod / RHF where used.
