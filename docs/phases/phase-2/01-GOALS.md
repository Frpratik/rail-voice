# Phase 2 — Goals & Success Criteria

## Goals

| ID | Goal |
|----|------|
| G1 | Real users can receive and verify OTP without knowing a shared mock code |
| G2 | Google Sign-In verifies cryptographically against Google when enabled |
| G3 | `APP_ENV=production` cannot boot with mock auth enabled |
| G4 | Rate limits survive multi-instance / redeploys via Redis |
| G5 | Security-relevant auth events are queryable for incident response |
| G6 | Staging remains developer-friendly (mocks optional, not default for prod) |

## Non-goals

- Changing issue/report UX beyond auth UI  
- Replacing Neon/Render/Vercel hosting  
- Implementing S3, push, or Celery beat on free tier  
- Full SIEM / OpenTelemetry (structured audit table is enough)

## Success criteria (acceptance)

- [x] With `OTP_MOCK_MODE=false` and provider credentials set, `POST /auth/otp/request` does **not** return `mock_otp`  
- [x] OTP verify works with SMS-delivered code (or provider sandbox) — code path + ConsoleSmsProvider  
- [x] With `GOOGLE_OAUTH_MOCK_MODE=false` and `GOOGLE_CLIENT_ID` set, invalid `id_token` → 401  
- [x] Valid Google token creates/links user and returns JWT (verify path)  
- [x] App refuses to start if production + mocks on  
- [x] OTP abuse from one IP is limited consistently when Redis is configured  
- [x] Refresh-token reuse still revokes family; event written to audit log  
- [x] Frontend hides mock OTP banner when API omits `mock_otp` / admin hint when `NEXT_PUBLIC_OTP_MOCK=false`  
- [x] Docs + env checklist updated; baseline docs link to Phase 2  

## Environments

| Env | Mocks | Redis rate limit | SMS |
|-----|-------|------------------|-----|
| Local | Optional (default on) | Optional (memory fallback) | Console/log provider |
| Staging (free) | Optional | Upstash free or memory | Provider sandbox |
| Production | **Forbidden** | **Required** | Live provider |
