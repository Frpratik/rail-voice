# Phase 2 — SMS OTP Design

## Current state (baseline)

- `AuthService.request_otp` stores hashed OTP; code is always `OTP_MOCK_CODE` when mock mode is on  
- Response may include `mock_otp` for UI  
- No external SMS send  

## Target state

```
Client → POST /auth/otp/request { mobile }
       → API generates secure 6-digit OTP
       → hash stored in otp_requests (TTL 5 min)
       → SmsProvider.send(mobile, message)
       → response: { message, expires_in_seconds, retry_after_seconds }
         (mock_otp only if OTP_MOCK_MODE=true)

Client → POST /auth/otp/verify { mobile, otp }
       → same verification as today (attempts ≤ 3)
```

## Provider abstraction

```python
class SmsProvider(Protocol):
    async def send_otp(self, mobile: str, otp: str) -> None: ...
```

| Provider | Env | Use |
|----------|-----|-----|
| `ConsoleSmsProvider` | local / CI | Logs OTP; no network |
| `TwilioSmsProvider` | staging/prod | Twilio Verify or Messages API |
| `Msg91SmsProvider` | India-friendly optional | MSG91 send OTP |

Config:

```
OTP_MOCK_MODE=false
SMS_PROVIDER=twilio|msg91|console
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=   # or Verify Service SID
MSG91_AUTH_KEY=
MSG91_TEMPLATE_ID=
OTP_TTL_SECONDS=300
OTP_LENGTH=6
```

## Generation

- Use `secrets.randbelow` / `secrets.choice` for digits — **never** fixed code in non-mock  
- Store only `hash_value(otp)` (existing)  
- Do not log raw OTP in production (console provider exception for local)

## API contract changes

| Field | Baseline | Phase 2 |
|-------|----------|---------|
| `mock_otp` | Present when mock | Present **only** when `OTP_MOCK_MODE=true` |
| Errors | Generic | `SMS_SEND_FAILED` (502/503) if provider fails after persist — or fail before persist (prefer: send then commit, or mark row failed) |

**Recommended:** generate + hash + flush OTP row, then send; if send fails, mark request unusable / delete and return 503 so user can retry.

## Rate limits (with Redis)

- Per mobile hash: e.g. 1 request / 60s, 5 / hour  
- Per IP: keep existing OTP bucket, tighten if needed  
- Align `retry_after_seconds` in response with limiter  

## Frontend

- Login page: show mock OTP hint **only** if API returns `mock_otp` or `NEXT_PUBLIC_OTP_MOCK=true`  
- Copy: “OTP sent to your mobile” without implying console codes in prod  

## Security notes

- Mobile pattern stays `^\+91\d{10}$` for v1 India scope  
- Consider hashing mobile in logs (already hashed at rest)  
- Do not return whether a mobile is registered (same message always)
