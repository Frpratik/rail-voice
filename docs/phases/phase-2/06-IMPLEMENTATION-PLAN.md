# Phase 2 — Implementation Plan

## Order of work

| Step | Work | Files (expected) |
|------|------|------------------|
| 1 | Config + production gates | `app/core/config.py`, `main.py` |
| 2 | SMS provider + OTP send path | `app/services/sms/`, `auth_service.py`, `auth.py` |
| 3 | Google non-mock only claims + flag | `auth.py`, `auth_service.py` |
| 4 | Redis rate limit backend | `app/core/rate_limit.py`, Redis client |
| 5 | Alembic `003` audit table + writer | `models/`, `services/audit.py`, hooks in auth |
| 6 | Frontend Google GIS + mock UI gates | `railvoice-web` login/auth pages |
| 7 | Env examples + FREE_DEPLOY / DEPLOY notes | `.env*`, `FREE_DEPLOY.md` |
| 8 | Tests | `tests/` OTP provider mock, Google verify mock, Redis optional |
| 9 | Docs: mark Phase 2 shipped; bump version | `docs/`, `main.py` version |

## Definition of done

All success criteria in [01-GOALS.md](01-GOALS.md) checked; CI green; staging env can run with mocks still for free demo **or** with sandbox SMS.

## Risk / rollback

| Risk | Mitigation |
|------|------------|
| SMS cost / delivery delay | Console + sandbox; timeout 10s |
| Redis unavailable on free | Memory fallback outside production |
| Google client ID misconfig | Feature flag off hides button |
| Breaking login UX | Keep OTP flow API-compatible |

## Explicit non-implementation this phase

No S3, no push notifications, no Celery requirement, no corridor expansion.
