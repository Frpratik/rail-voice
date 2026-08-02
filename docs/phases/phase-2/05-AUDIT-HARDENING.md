# Phase 2 — Audit Logging & Hardening

## Audit events

New table `auth_audit_events` (Alembic `003`):

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| created_at | timestamptz | |
| event_type | string | see enum below |
| actor_user_id | UUID nullable | |
| mobile_hash | string nullable | |
| ip | string nullable | |
| user_agent | string nullable | |
| success | bool | |
| detail | jsonb | non-secret metadata only |

### Event types

| event_type | When |
|------------|------|
| `otp.request` | OTP requested |
| `otp.verify.success` | OTP verified |
| `otp.verify.fail` | Bad OTP / expired |
| `google.login` | Google auth success/fail |
| `token.refresh` | Refresh issued |
| `token.refresh.reuse` | Reuse detected → family revoke |
| `logout` | Logout / revoke |

**Never store:** raw OTP, access JWT, refresh plaintext, full Google token.

## Hardening checklist

| Item | Action |
|------|--------|
| Production mocks | Refuse boot if `OTP_MOCK_MODE` or `GOOGLE_OAUTH_MOCK_MODE` |
| Secret strength | Warn/fail if `SECRET_KEY` default or short |
| Refresh cookie | `Secure`, `HttpSameSite=lax`, path scoped (already); document HTTPS-only |
| CORS | Production origins exact list; no `*` |
| Admin seed | Document rotate free-tier demo admin password / mobile |
| Neon password | Rotate if ever pasted in chat/logs |
| Response headers | Optional: `X-Content-Type-Options`, `Referrer-Policy` via middleware |

## Observability

- Structured log line per audit write (same fields)  
- Admin-only future endpoint deferred; DB query sufficient for Phase 2  

## Refresh hardening (small)

- Confirm family revoke on reuse (already) + audit  
- Optional: bind refresh to user-agent hash soft-check (warn only, not block) — **optional**, skip if timeboxed
