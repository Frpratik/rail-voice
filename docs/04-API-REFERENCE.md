# 4. API Reference

**Base URL (prod):** `https://rail-voice.onrender.com`  
**API prefix:** `/api/v1`  
**Interactive docs:** `/docs` (Swagger), `/redoc`  
**Response shape (JSON):** `{ "data": ..., "meta": { "correlation_id", "timestamp" } }`

Browser production traffic typically goes via Vercel proxy: `https://rail-voice.vercel.app/api/v1/...`.

---

## 4.1 Conventions

| Item | Detail |
|------|--------|
| Auth Bearer | `Authorization: Bearer <access_token>` |
| Anonymous | Header `X-Anonymous-Session: <uuid>` on write flows |
| Cookies | `refresh_token` HttpOnly, path `/api/v1/auth` |
| Errors | HTTP status + `detail` string or object (`code`, `message`, …) |
| Rate limits | Headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`; 429 when exceeded |
| Correlation | `X-Correlation-Id` request/response |

### Auth dependency legend

- **Public** — no auth  
- **Reporter** — JWT or anonymous session (`get_reporter_user`)  
- **User** — authenticated user (`get_current_user`); comments reject anonymous  
- **Official** — JWT + official role (`require_official`)

---

## 4.2 Health & ops (root)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | Public | Liveness |
| GET | `/health/ready` | Public | DB connectivity |
| GET | `/metrics` | Public | Prometheus metrics |
| GET | `/media/{key…}` | Public | Uploaded media |

---

## 4.3 Auth — `/api/v1/auth`

| Method | Path | Auth | Body / notes |
|--------|------|------|----------------|
| POST | `/auth/otp/request` | Public | `{ "mobile": "+91##########" }` — mock returns `mock_otp` |
| POST | `/auth/otp/verify` | Public | `{ "mobile", "otp" }` → access + refresh + user |
| POST | `/auth/google` | Public | `{ "id_token", email?, name?, google_id?, avatar_url? }` |
| POST | `/auth/refresh` | Cookie/body | `{ "refresh_token"? }` → rotated tokens |
| POST | `/auth/anonymous` | Public | → `anonymous_session_id` + limits |
| POST | `/auth/logout` | User | 204; revokes refresh family |

---

## 4.4 Stations & issues

| Method | Path | Auth | Query / body |
|--------|------|------|----------------|
| GET | `/stations` | Public | `zone_code`, `search` |
| GET | `/stations/{code}` | Public | Open issue count included |
| GET | `/issues` | Public | `station_code`, `sort`=`newest\|most_supported\|ai_priority\|trending`, `limit` |
| GET | `/issues/{id}` | Public | Issue + timeline + comments |
| POST | `/issues/check-duplicates` | Reporter | `{ description, station_id, title? }` |
| POST | `/issues` | Reporter | Create; 409 `DUPLICATE_FOUND` if similar & not forced |
| POST | `/issues/{id}/support` | Reporter | Idempotent conflict if already supported |
| GET | `/issues/{id}/comments` | Public | |
| POST | `/issues/{id}/comments` | User (non-anon) | `{ body, parent_id? }` |
| POST | `/issues/{id}/photos` | Reporter (owner/official) | `multipart/form-data` field `file` |
| PATCH | `/comments/{id}/hide` | Official | Moderation |

### Create issue body

```json
{
  "description": "string (20–5000)",
  "station_id": "uuid",
  "title": "string?",
  "platform_id": "uuid?",
  "train_number": "string?",
  "coach_number": "string?",
  "latitude": 0,
  "longitude": 0,
  "force_create": false,
  "divergence_reason": "required if force_create (min 10)"
}
```

### Duplicate check response (concept)

```json
{
  "has_similar": true,
  "threshold": 0.82,
  "similar_issues": [ { "id", "issue_number", "similarity", "support_count", "…" } ],
  "recommendation": "support_existing | create_new"
}
```

---

## 4.5 Search — `/api/v1/search`

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/search` | Public | `q`, `station_id?`, `limit` — hybrid |
| POST | `/search/semantic` | Public | `{ query, station_id?, limit }` |

---

## 4.6 Notifications — `/api/v1/notifications`

| Method | Path | Auth |
|--------|------|------|
| GET | `/notifications` | User → `{ items, unread_count }` |
| PATCH | `/notifications/{id}/read` | User |
| POST | `/notifications/read-all` | User |

---

## 4.7 Admin — `/api/v1/admin`

All require **Official**.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/dashboard` | KPIs + top priority issues |
| GET | `/admin/issues` | Queue; `status_filter?`, `limit` |
| PATCH | `/admin/issues/{id}/status` | `{ status, remarks, visibility }` |
| POST | `/admin/issues/{id}/assign` | `{ assignee_id, remarks }` |
| POST | `/admin/issues/{id}/escalate` | `{ target: station_manager\|division\|zone, remarks }` |
| GET | `/admin/officers` | Assignable officials |
| GET | `/admin/reports/issues.xlsx` | Excel download |
| GET | `/admin/reports/issues.pdf` | PDF download |
| GET | `/admin/analytics/ai-insights/daily-summary` | AI daily summary |
| GET | `/admin/spam-queue` | Spam-held issues |

---

## 4.8 Example — OTP (staging / mock)

```http
POST /api/v1/auth/otp/request
Content-Type: application/json

{"mobile":"+919876543210"}
```

```http
POST /api/v1/auth/otp/verify
Content-Type: application/json

{"mobile":"+919876543210","otp":"123456"}
```

Super admin seed: mobile `+919999999999`, OTP `123456` (mock mode).

---

## 4.9 Client mapping

Frontend client: `railvoice-web/src/lib/api.ts` namespaces `api.auth`, `api.issues`, `api.stations`, `api.notifications`, `api.admin`.
