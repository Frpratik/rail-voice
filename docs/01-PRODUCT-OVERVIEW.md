# 1. Product Overview

## 1.1 Vision

RailVoice is a citizen-facing and operations-facing platform for reporting and resolving public issues on Indian Railways, starting with **Western Railway (WR) — Churchgate → Virar**.

Passengers report problems (cleanliness, safety, facilities, punctuality, accessibility). The system uses **AI** to detect duplicates, categorize, score severity/spam/priority, and help railway officials triage work.

## 1.2 Problem statement

- Passengers lack a transparent, station-aware channel to raise issues that others can support.
- Duplicate reports flood channels without semantic matching.
- Officials need prioritized queues, assignment, escalation, and exportable reports.
- Anonymous reporting must be possible with abuse controls.

## 1.3 Personas

| Persona | Goals | Primary surfaces |
|---------|-------|------------------|
| Passenger | Report issues, support others, track updates | Web app: feed, report, issue detail, login |
| Anonymous reporter | Quick report without account | Report flow + `X-Anonymous-Session` |
| Station / ops official | Triage, assign, escalate, export | `/admin/*` |
| Super admin | Full ops access (seeded) | Same admin console |

## 1.4 Core product capabilities (baseline)

### Passenger

- Browse public issues (newest / most supported / priority / trending)
- Station directory (29 WR stations seeded)
- Report with duplicate detection (support existing or force-create with reason)
- Support (upvote) issues
- Photos on report / issue detail
- Comments (signed-in users)
- In-app notifications
- Auth: mobile OTP (mock in staging), Google (mock or real), anonymous session
- Profile + entry to ops console when official roles present

### Operations

- Dashboard KPIs + AI priority queue
- Issue queue with status transitions
- Assign officer, escalate to station manager / division / zone
- PDF and Excel exports
- Spam queue + daily AI summary endpoint
- Role-gated access (`require_official`)

### Platform

- PostgreSQL + **pgvector** semantic similarity
- Rate limiting, refresh-token rotation, CORS, Prometheus metrics
- Free deploy: Vercel + Render + Neon
- Optional VPS path: Docker Compose + Nginx

## 1.5 Explicit non-goals (baseline)

These were designed or partially stubbed but are **out of scope** for “done” baseline completeness:

- Production SMS OTP provider (mock used on free/staging)
- Full Google Identity production hardening (mock available)
- Durable object storage (S3) — local/ephemeral disk on free Render
- Push (FCM) / email delivery
- Native mobile apps
- Full RailMadad integration
- Location-scoped RBAC enforcement on every admin query
- Complete Phase-5 endpoint surface (~80 designed; subset implemented)

See [11-BASELINE-SCOPE.md](11-BASELINE-SCOPE.md).

## 1.6 Success metrics (suggested)

| Metric | Why |
|--------|-----|
| Duplicate-support rate vs new creates | AI duplicate UX working |
| Time-to-first-official-action | Ops triage |
| Support count / trending | Engagement |
| Spam auto-hold rate + false positives | AI quality |
| API p95 latency / cold starts | Free-tier realism |

## 1.7 Domain vocabulary

| Term | Meaning |
|------|---------|
| Issue | Citizen-reported problem at a station/context |
| Support | Endorsement that increases visibility / priority |
| Duplicate check | Semantic + lexical similarity before create |
| Divergence reason | Required text when forcing create despite similars |
| Timeline | Auditable status / assign / escalate / comment events |
| Official | User with ops role (moderator → super_admin) |
