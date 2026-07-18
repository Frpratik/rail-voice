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

## 11.4 Suggested Phase 2 themes (for next doc pack)

Pick explicitly before building; then produce `docs/phases/phase-2/README.md`:

1. **Trust & auth** — real OTP + Google; remove mocks in prod  
2. **Media** — S3, CDN, scan pipeline  
3. **Ops depth** — scoped queues, merge, SLA, richer analytics  
4. **Reliability** — paid always-on API, Redis rate limits, backups  
5. **Quality** — E2E tests, AI eval dashboards  

## 11.5 Versioning

| Field | Value |
|-------|-------|
| Baseline doc version | 1.0.0 |
| App version (API) | 1.0.0 (`app/main.py`) |
| Schema head | Alembic `002` |

When Phase 2 ships, bump product version and add a changelog entry linking to the new phase docs.
