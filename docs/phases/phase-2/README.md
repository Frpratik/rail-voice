# Phase 2 — Production Trust

**Status:** Implemented (API 1.1.0)  
**Depends on:** Baseline Release 1.0.0 (`docs/`)  
**Product version:** 1.1.0  
**Theme:** Make authentication and abuse controls safe for real users

---

## Document index

| Doc | Purpose |
|-----|---------|
| [README.md](README.md) | This overview |
| [01-GOALS.md](01-GOALS.md) | Goals, non-goals, success criteria |
| [02-AUTH-OTP.md](02-AUTH-OTP.md) | Real SMS OTP design |
| [03-AUTH-GOOGLE.md](03-AUTH-GOOGLE.md) | Production Google Sign-In |
| [04-RATE-LIMITS.md](04-RATE-LIMITS.md) | Redis-backed rate limiting |
| [05-AUDIT-HARDENING.md](05-AUDIT-HARDENING.md) | Audit log, env gates, secrets |
| [06-IMPLEMENTATION-PLAN.md](06-IMPLEMENTATION-PLAN.md) | Work breakdown + acceptance |
| [07-ENV-CHECKLIST.md](07-ENV-CHECKLIST.md) | Staging vs production env vars |
| [08-TEST-PLAN.md](08-TEST-PLAN.md) | Phase 2 test cases |

---

## Shipped

1. SMS OTP via pluggable provider (`console` / `twilio` / `msg91`)  
2. Google ID token verification when mock is off; `GOOGLE_AUTH_ENABLED` flag  
3. Production startup refuses mocks, console SMS, weak secrets, missing Redis (when required)  
4. Redis rate limits with memory fallback; per-mobile OTP hour cap  
5. `auth_audit_events` table (Alembic `003`)  
6. Frontend: Google Identity Services when `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set  

Free staging can keep mocks (`APP_ENV=staging`). See [07-ENV-CHECKLIST.md](07-ENV-CHECKLIST.md).
