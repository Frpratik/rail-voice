# 10. Testing Strategy

## 10.1 Test pyramid

| Layer | Location | Focus |
|-------|----------|-------|
| Unit (AI) | `tests/test_ai.py`, `test_ai_eval.py` | Embeddings, categorizer, spam, duplicate pairs |
| Integration API | `test_api`, `test_auth`, `test_admin`, `test_search`, `test_security` | HTTP flows against seeded DB |
| Load smoke | `tests/load/smoke.js` (k6) | Health + stations |
| Plan | `tests/TEST_PLAN.md` | Coverage & critical paths |
| CI | `.github/workflows/ci.yml` | pytest cov ≥ 55%, frontend build/lint |

## 10.2 Running tests locally

```bash
cd railvoice-backend
# DB up (compose postgres) + env
alembic upgrade head
python -m app.scripts.seed
PYTHONPATH=. pytest -v --cov=app --cov-fail-under=55
```

Fixtures (`conftest.py`) expect seeded stations (e.g. Bandra) and admin mobile.

## 10.3 Critical paths covered

- OTP request/verify, anonymous session, logout authz  
- Stations list, duplicate check → create/support  
- Admin dashboard/status; passenger forbidden on admin  
- Hybrid / semantic search  
- AI unit behaviors and duplicate-pair eval tiers  

## 10.4 Gaps / next tests

- Photo upload multipart  
- Comment + notification flows  
- Refresh token reuse detection  
- Assign / escalate / report downloads  
- Frontend E2E (Playwright) against staging  

## 10.5 Manual QA script (staging)

1. Open https://rail-voice.vercel.app — feed shows stations/issues  
2. Report issue ≥20 chars — duplicate sheet or create  
3. Support issue  
4. Login OTP — comment  
5. Super admin — admin dashboard, status update, export  
6. Upload photo on issue detail
