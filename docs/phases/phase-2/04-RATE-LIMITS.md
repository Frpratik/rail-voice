# Phase 2 — Redis Rate Limiting

## Current state

`RateLimitMiddleware` uses in-memory counters. Multiple Render instances / restarts reset buckets; free single instance is weak but usable for demos.

## Target state

```
RateLimitBackend
  ├── MemoryRateLimitBackend   # default when REDIS_URL unset / local
  └── RedisRateLimitBackend    # fixed-window or sliding INCR + EXPIRE
```

Settings:

```
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=auto|memory|redis   # auto: redis if REDIS_URL else memory
REDIS_URL=redis://...                  # Upstash rediss://...
RATE_LIMIT_OTP_PER_MINUTE=5
RATE_LIMIT_WRITE_PER_MINUTE=30
RATE_LIMIT_DEFAULT_PER_MINUTE=120
# Phase 2 additions:
RATE_LIMIT_OTP_PER_MOBILE_PER_HOUR=5
RATE_LIMIT_REQUIRE_REDIS_IN_PRODUCTION=true
```

## Key schema

```
rl:{scope}:{key}:{window}
# examples
rl:ip:otp:203.0.113.1:202607181430
rl:mobile:otp:{sha256(mobile)}:2026071814   # hour window
```

## Behavior

- On limit: HTTP **429**, `Retry-After` seconds, JSON error code `RATE_LIMITED`  
- Redis down:  
  - **Production:** fail closed for OTP routes (503) or fail open for reads (document choice: **fail open for GET, fail closed for OTP**)  
  - **Non-prod:** fall back to memory + log warning  

## Production gate

If `APP_ENV=production` and `RATE_LIMIT_REQUIRE_REDIS_IN_PRODUCTION=true`, startup requires reachable Redis (ping).

## Nginx note

VPS deploy may keep Nginx `limit_req` as defense-in-depth; Redis is the app-layer source of truth across workers.
