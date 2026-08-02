# Phase 3 — Advanced Ops & Durable Evidence

**Status:** Shipped with code (API 1.2.0)  
**Depends on:** Phase 2 (Production Trust) · Baseline 1.0  
**Product version:** 1.2.0  
**Theme:** Close the biggest gaps from the original RailVoice master vision for civic reporting + official triage

---

## Why this phase

The original master command required a production-grade platform where passengers report with evidence, AI reduces duplicates, and officials triage with trustworthy queues and KPIs. Baseline + Phase 2 delivered core UX and auth trust. Still missing from that vision (and highest impact now):

| Gap | User impact |
|-----|-------------|
| Ephemeral photo disk | Evidence disappears on free-tier redeploy |
| No admin merge | Duplicate noise stays in ops queues |
| Unscoped admin queues | Station staff see the whole corridor |
| Stub SLA KPIs | Dashboard numbers are not operational |
| Search API unused | Passengers cannot find issues by text |

## In scope (this sprint)

1. **Durable media** — S3/R2-compatible backend behind `StorageService` (local still default)  
2. **Admin merge** — `POST /admin/issues/{id}/merge` + queue UI  
3. **Location-scoped RBAC** — filter dashboard/queue/reports/spam by officer scope  
4. **Real SLA KPIs** — avg resolution hours + open breaches by severity  
5. **Passenger search UI** — wire existing `GET /search` into the home feed  

## Out of scope (later)

- RailMadad API sync  
- FCM / email push delivery  
- Virus scanning / thumbnails / presigned upload flow  
- Full analytics heatmap suite  
- Native mobile apps  

## Docs

| Doc | Purpose |
|-----|---------|
| [README.md](README.md) | This overview |
| [01-GOALS.md](01-GOALS.md) | Goals & acceptance |
| [02-FEATURES.md](02-FEATURES.md) | Feature design notes |
| [03-ENV.md](03-ENV.md) | Storage + SLA env vars |
