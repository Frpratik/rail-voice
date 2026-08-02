# Phase 2 — Environment Checklist

## Local (developer)

```
APP_ENV=development
OTP_MOCK_MODE=true
GOOGLE_OAUTH_MOCK_MODE=true
SMS_PROVIDER=console
REDIS_URL=   # empty → memory rate limits
GOOGLE_AUTH_ENABLED=true
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
NEXT_PUBLIC_OTP_MOCK=true
```

## Staging (free Render / Vercel)

Option A — keep demo mocks (current free path):

```
APP_ENV=staging
OTP_MOCK_MODE=true
GOOGLE_OAUTH_MOCK_MODE=true
```

Option B — trust rehearsal:

```
APP_ENV=staging
OTP_MOCK_MODE=false
SMS_PROVIDER=twilio
TWILIO_*=sandbox
GOOGLE_OAUTH_MOCK_MODE=false
GOOGLE_CLIENT_ID=...
REDIS_URL=rediss://...upstash...
NEXT_PUBLIC_GOOGLE_CLIENT_ID=...
NEXT_PUBLIC_OTP_MOCK=false
```

## Production

```
APP_ENV=production
OTP_MOCK_MODE=false          # required
GOOGLE_OAUTH_MOCK_MODE=false # required
SMS_PROVIDER=twilio|msg91
TWILIO_* or MSG91_*          # required for OTP
GOOGLE_AUTH_ENABLED=true
GOOGLE_CLIENT_ID=...         # required if Google enabled
REDIS_URL=...                # required if RATE_LIMIT_REQUIRE_REDIS_IN_PRODUCTION
SECRET_KEY=<long random>
CORS_ORIGINS=https://your-domain
CELERY_ENABLED=false|true    # independent
NEXT_PUBLIC_OTP_MOCK=false
NEXT_PUBLIC_GOOGLE_CLIENT_ID=...
```

## Secrets never commit

- Twilio / MSG91 keys  
- `SECRET_KEY`  
- Database URL passwords  
- Google client secret (not needed for ID token verify; keep OAuth client restricted in Google Console)
