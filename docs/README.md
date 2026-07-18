# RailVoice Documentation

**Product:** AI-powered public issue reporting for Indian Railways  
**Documentation scope:** Completed baseline (MVP → production-capable free deploy)  
**Version:** 1.0.0-baseline  
**Last updated:** July 2026  
**Repository:** [github.com/Frpratik/rail-voice](https://github.com/Frpratik/rail-voice)

---

## Document index

| # | Document | Audience |
|---|----------|----------|
| 1 | [Product Overview](01-PRODUCT-OVERVIEW.md) | Product, stakeholders, new engineers |
| 2 | [System Architecture](02-ARCHITECTURE.md) | Engineers, architects |
| 3 | [Data Model](03-DATA-MODEL.md) | Backend engineers, DBAs |
| 4 | [API Reference](04-API-REFERENCE.md) | Frontend, integrators, QA |
| 5 | [AI Module](05-AI-MODULE.md) | ML/backend engineers |
| 6 | [Authentication & Security](06-AUTH-SECURITY.md) | Security, backend |
| 7 | [Frontend Application](07-FRONTEND.md) | Frontend engineers, designers |
| 8 | [Deployment](08-DEPLOYMENT.md) | DevOps, release owners |
| 9 | [Operations Runbook](09-OPERATIONS.md) | On-call, ops |
| 10 | [Testing Strategy](10-TESTING.md) | QA, engineers |
| 11 | [Baseline Scope & Roadmap](11-BASELINE-SCOPE.md) | Product, planning |

---

## Quick links

| Environment | URL |
|-------------|-----|
| Web (production free) | https://rail-voice.vercel.app |
| API (production free) | https://rail-voice.onrender.com |
| OpenAPI docs | https://rail-voice.onrender.com/docs |
| Health | https://rail-voice.onrender.com/health |
| Readiness | https://rail-voice.onrender.com/health/ready |
| GitHub | https://github.com/Frpratik/rail-voice |

---

## Repository layout

```
RailVoice/
├── docs/                    ← You are here
├── railvoice-backend/       FastAPI + AI + Celery
├── railvoice-web/           Next.js App Router UI
├── deploy/                  Nginx, Render env examples, Prometheus
├── scripts/                 Render monorepo build/start helpers
├── docker-compose.yml       Local full stack
├── docker-compose.prod.yml  VPS / production compose
├── render.yaml              Render Blueprint
├── FREE_DEPLOY.md           Free-tier step guide
├── DEPLOY.md                VPS runbook
└── README.md                Project entry
```

---

## How to use this documentation

1. **New hire / stakeholder** → start with Product Overview, then Architecture.  
2. **Backend work** → Data Model, API Reference, Auth & Security, AI Module.  
3. **Frontend work** → Frontend Application + API Reference.  
4. **Ship / debug prod** → Deployment + Operations.  
5. **Next product phase** → Baseline Scope & Roadmap (what is in / out of this baseline).

Subsequent phases should add a dated folder or appendix (e.g. `docs/phases/phase-2/`) rather than overwriting this baseline unless a breaking change requires a version bump.
