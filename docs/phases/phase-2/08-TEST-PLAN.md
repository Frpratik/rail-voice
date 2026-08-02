# Phase 2 — Test Plan

## Unit / API

| ID | Case | Expect |
|----|------|--------|
| T1 | Mock OTP request | Response may include `mock_otp`; no SMS call |
| T2 | Non-mock OTP request with ConsoleSms | No `mock_otp`; provider `send_otp` called |
| T3 | OTP verify success | Tokens + audit `otp.verify.success` |
| T4 | OTP verify wrong code ×3 | Locked / fail; audit fails |
| T5 | SMS provider raises | 503; no usable OTP left |
| T6 | Google mock token (mock on) | 200 |
| T7 | Google bad token (mock off) | 401 |
| T8 | Production settings + OTP mock | `validate_for_runtime` / lifespan error |
| T9 | Rate limit OTP exceeded (memory) | 429 |
| T10 | Rate limit OTP exceeded (Redis) | 429 shared key (skip if no Redis in CI) |
| T11 | Refresh reuse | Family revoked + audit `token.refresh.reuse` |

## Frontend (manual)

| ID | Case |
|----|------|
| F1 | Mock mode: OTP hint visible |
| F2 | Non-mock: no fixed `123456` hint |
| F3 | Google button hidden without client ID |
| F4 | Google button with GIS returns real `id_token` to API |

## CI

- Keep pytest green without real Twilio/Google (mock providers)  
- Optional job marker `@pytest.mark.redis` skipped by default
