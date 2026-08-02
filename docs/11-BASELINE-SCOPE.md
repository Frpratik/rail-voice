# 11. Baseline Scope & Roadmap

## 11.1 Naming

This documentation freezes the **Baseline Release** (also called MVP / Phase-1 product delivery in planning chats). It includes design phases 1–10 work products plus implementation of core APIs/UI, gap features (photos, comments, notifications, Google mock, refresh, rate limits, admin assign/escalate/reports), and free-tier deployment.

Future work starts a **new phase document set** under e.g. `docs/phases/phase-2/` without erasing this baseline.

## 11.2 In scope (delivered)

### Product

- Passenger feed, report, duplicate UX, support, issue detail  
- Stations (WR corridor seed)  
- Auth: OTP mock, Google mock, anonymous  
- Notifications UI + API  
- Comments + photos  
- Admin dashboard, queue, assign, escalate, PDF/Excel  

### Engineering

- FastAPI modular monolith + Alembic  
- pgvector duplicate/search path  
- Sync AI pipeline  
- Next.js premium UI  
- Docker local + Compose prod templates  
- Free deploy: Vercel + Render + Neon  
- CI: pytest + frontend build  
- Ops docs: FREE_DEPLOY, DEPLOY, this `docs/` suite  

## 11.3 Out of scope / deferred

| Item | Notes |
|------|-------|
| Real SMS OTP | Needs provider + cost |
| Production Google OAuth only | Client ID + disable mock |
| S3 / durable media | Free disk is ephemeral |
| Celery on free tier | Optional on VPS |
| Push/email | Notification rows only |
| Full designed REST surface | Many Phase-5 endpoints unused |
| Location-scoped admin RBAC | Columns exist; not fully enforced |
| Merge duplicates / RailMadad | Partial model only |
| Mobile apps | Web only |
| SLA KPI accuracy | Dashboard fields partly stubbed |
| Hardened prod APP_ENV | Staging mocks on free |

## 11.4 Phase 2 (shipped)

**Theme:** Trust & auth (production trust) — API **1.1.0**, schema Alembic **003**.

Documentation: [`docs/phases/phase-2/`](phases/phase-2/README.md)

## 11.4b Phase 3 (shipped)

**Theme:** Advanced ops & durable evidence — API **1.2.0**.

- S3/R2 storage backend  
- Admin duplicate merge  
- Location-scoped admin queues  
- Real SLA KPIs  
- Passenger search UI  

Documentation: [`docs/phases/phase-3/`](phases/phase-3/README.md)

Later candidates:

4. **Reliability** — paid always-on API, backups  
5. **Quality** — E2E tests, AI eval dashboards  
6. **Integrations** — RailMadad, push/email  

## 11.5 Versioning

| Field | Value |
|-------|-------|
| Baseline doc version | 1.0.0 |
| App version (API) | 1.2.0 (`app/main.py`) |
| Schema head | Alembic `003` |
