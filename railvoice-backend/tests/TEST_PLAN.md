# RailVoice Test Plan (Phase 10)

## Test Pyramid

| Layer | Tool | Location | Count |
|-------|------|----------|-------|
| Unit | pytest | `tests/test_ai.py`, `tests/test_ai_eval.py` | 7+ |
| Integration | pytest + httpx | `tests/test_*.py` | 15+ |
| E2E | Manual / Playwright (planned) | `railvoice-web` | — |
| Load | k6 / Locust (planned) | `tests/load/` | — |

## Run Locally

```bash
# Requires PostgreSQL + Redis + seed
cd railvoice-backend
alembic upgrade head
python -m app.scripts.seed
PYTHONPATH=. pytest -v --cov=app
```

## Critical Paths (Must Pass)

1. **Auth** — OTP request/verify, anonymous session, logout guard
2. **Issue lifecycle** — create → support → admin verify
3. **Search** — multi-term text search returns results
4. **Admin RBAC** — passenger 403, official 200

## E2E Manual Checklist

- [ ] Report issue at Bandra → appears in feed
- [ ] Support existing issue → count increments
- [ ] Login OTP → profile shows user
- [ ] Admin dashboard loads for official
- [ ] Dark mode toggle works
- [ ] Station page lists issues

## Security Checklist (OWASP)

- [x] JWT required for protected routes
- [x] RBAC on admin endpoints
- [x] Input validation (Pydantic min length)
- [x] OTP brute-force limit (3 attempts)
- [ ] Rate limiting middleware (planned)
- [ ] CORS production whitelist
- [ ] File upload virus scan

## Load Test Targets

| Endpoint | Target p95 | Concurrent users |
|----------|------------|------------------|
| GET /issues | < 200ms | 500 |
| POST /issues/check-duplicates | < 1.5s | 100 |
| POST /issues | < 3s | 50 |
| GET /search | < 500ms | 200 |

## Coverage Gate

CI enforces **≥ 55%** line coverage on `app/` (MVP). Target 80% for production.
