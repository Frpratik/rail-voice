# 6. Authentication & Security

## 6.1 Auth methods

| Method | Use | Tokens |
|--------|-----|--------|
| Mobile OTP | Primary passenger login | Access JWT + refresh |
| Google ID token | OAuth / mock | Same |
| Anonymous session | Report/support without account | UUID header only |
| Refresh rotation | Session continuity | Opaque refresh + family |

## 6.2 Token details

| Token | Type | Lifetime (default) | Storage |
|-------|------|--------------------|---------|
| Access | JWT HS256, `type=access` | 15 minutes | Frontend `localStorage` / `access_token` |
| Refresh | Opaque random, SHA-256 stored | 7 days | HttpOnly cookie + returned in JSON for SPA |

Refresh **rotation**: new token same `family_id`; reuse of revoked token revokes entire family.

## 6.3 Headers & cookies

```
Authorization: Bearer <access>
X-Anonymous-Session: <uuid>     # writes when no Bearer
Cookie: refresh_token=...       # path=/api/v1/auth
```

## 6.4 Role-based access

- Passenger APIs: public or reporter/user as documented  
- Admin APIs: `require_official` — volunteer and above  
- Frontend ops link: moderator and above (see Profile)  
- Comments: signed-in non-anonymous only  

## 6.5 Rate limiting

Middleware: `app/core/rate_limit.py` (in-memory buckets per instance).

| Bucket | Default |
|--------|---------|
| OTP request | 5 / min / IP |
| Writes | 30 / min / IP |
| Reads | 120 / min / IP |

Returns **429** with `Retry-After`. Nginx (VPS) can add another auth zone.

## 6.6 Product abuse controls

- Anonymous daily issue cap (`ANONYMOUS_DAILY_ISSUE_LIMIT`, default 3)  
- OTP attempt limit (3)  
- Spam auto-hold hides from public feed  
- Photo MIME/size validation  
- Max photos per issue (default 5)  

## 6.7 CORS

Configured origins from `CORS_ORIGINS`. Non-prod adds localhost:3000/3001.  
Production free: includes `https://rail-voice.vercel.app`.  
Credentials allowed; explicit allow-headers include `Authorization`, `X-Anonymous-Session`.

## 6.8 Production hardening gates

When `APP_ENV=production`, startup fails if:

- Weak `SECRET_KEY` (< 32 chars / known placeholders)  
- `OTP_MOCK_MODE=true`  
- `GOOGLE_OAUTH_MOCK_MODE=true`  
- Empty `CORS_ORIGINS`  

Free deploy uses `APP_ENV=staging` so mocks remain usable.

## 6.9 Secrets handling

- Never commit `.env`, `.env.local`, `.env.production`  
- Neon passwords exposed in chat must be **rotated**  
- Prefer env injection on Render/Vercel; rotate `SECRET_KEY` on compromise (forces re-login)

## 6.10 Security backlog (next phases)

- Real SMS OTP + Google client verification only  
- S3 + signed URLs; virus scan beyond MIME  
- Restrict `/docs` and `/metrics` publicly  
- Redis-backed distributed rate limits  
- Enforce location-scoped RBAC on admin lists  
- CSP headers, refresh cookie SameSite strategy for multi-domain
