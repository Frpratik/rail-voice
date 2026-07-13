# Free deployment (no paid server needed)

Best free combo for RailVoice:

| Layer | Service | Cost | Your status |
|-------|---------|------|-------------|
| Frontend | [Vercel](https://vercel.com) | Free | **Done** → https://rail-voice.vercel.app |
| Postgres + pgvector | [Neon](https://neon.tech) | Free | **Do this next** |
| API | [Render](https://render.com) Web Service | Free | After Neon |

Cold start: first request to Render after idle can take 30–60s. That’s normal on free.

---

## Order

1. ~~Vercel (frontend)~~ ✅ https://rail-voice.vercel.app  
2. **Neon (database)** ← you are here  
3. Render (API) + wire Vercel `NEXT_PUBLIC_API_URL`

Repo: https://github.com/Frpratik/rail-voice

---

## 1. Neon (database) — do this now

### A. Create project

1. Open https://console.neon.tech and sign up / log in  
2. **New Project**
   - Name: `railvoice` (any name)
   - Region: closest to you
   - Postgres version: default is fine  
3. Create project and wait until it’s ready  

### B. Enable pgvector (required)

1. Open **SQL Editor**  
2. Paste and **Run**:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Confirm:

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

You should see one row with `vector`.

### C. Copy connection strings

1. Dashboard → your project → **Connect** / **Connection details**  
2. Prefer the **pooled** connection if Neon shows both  
3. Copy the connection string (looks like `postgresql://…@….neon.tech/neondb?sslmode=require`)

From that **one** string, make **two** variants for Render later:

```text
# 1) Sync — keep as-is (or ensure sslmode=require)
postgresql://USER:PASSWORD@HOST/neondb?sslmode=require

# 2) Async — only change the scheme + ssl query param
postgresql+asyncpg://USER:PASSWORD@HOST/neondb?ssl=require
```

Tips:
- Same `USER`, `PASSWORD`, `HOST`, database name in both  
- Sync uses `sslmode=require`  
- Async uses `postgresql+asyncpg://` and `ssl=require` (not `sslmode`)  
- If the password has special characters, keep Neon’s URL-encoded form  

### D. Save for Render (scratch pad — do not commit)

```env
DATABASE_URL=postgresql+asyncpg://...neon.tech/neondb?ssl=require
DATABASE_URL_SYNC=postgresql://...neon.tech/neondb?sslmode=require
```

When Neon is done, say **“Neon done”** (you can paste the redacted host if you want a double-check) and we’ll do Render next.

---

## 2. Render (API) — after Neon

1. Sign up with GitHub: https://dashboard.render.com  
2. **New → Web Service** → select **Frpratik/rail-voice**  
3. Settings (whole repo — no Root Directory needed):

| Field | Value |
|-------|--------|
| Repository | `Frpratik/rail-voice` (whole project is fine) |
| Runtime | Python 3 |
| Build Command | `bash scripts/render_build.sh` |
| Start Command | `bash scripts/render_start.sh` |
| Instance type | **Free** |
| Env `PYTHON_VERSION` | `3.12.8` |

If shell scripts fail on Windows line endings, use these instead:

| Field | Value |
|-------|--------|
| Build Command | `pip install -r railvoice-backend/requirements.txt` |
| Start Command | `cd railvoice-backend && bash scripts/free_boot.sh` |

4. Environment → **Add from .env** — paste this (fill Neon + `SECRET_KEY` first):

```env
APP_ENV=staging
DEBUG=false
SECRET_KEY=REPLACE_WITH_LONG_RANDOM_32_PLUS_CHARS
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST/neondb?ssl=require
DATABASE_URL_SYNC=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
CELERY_ENABLED=false
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
REDIS_URL=
OTP_MOCK_MODE=true
OTP_MOCK_CODE=123456
GOOGLE_OAUTH_MOCK_MODE=true
RUN_SEED=true
CORS_ORIGINS=https://rail-voice.vercel.app,http://localhost:3000
PUBLIC_BASE_URL=https://REPLACE_WITH_YOUR_SERVICE.onrender.com
LOCAL_STORAGE_PATH=storage/uploads
STORAGE_BACKEND=local
RATE_LIMIT_ENABLED=true
```

Same file: [`deploy/render.env.example`](deploy/render.env.example)

5. Deploy → note API URL → set `PUBLIC_BASE_URL` → **Manual Deploy**  
6. Test:

```bash
curl https://YOUR-RENDER-SERVICE.onrender.com/health
curl https://YOUR-RENDER-SERVICE.onrender.com/health/ready
```

Super admin (after seed): `+919999999999` / OTP `123456`.

---

## 3. Point Vercel at the API

Vercel → Settings → Environment Variables:

```text
NEXT_PUBLIC_API_URL=https://YOUR-RENDER-SERVICE.onrender.com/api/v1
```

Redeploy Vercel. CORS already includes `https://rail-voice.vercel.app`.

---

## Smoke test

- [ ] https://rail-voice.vercel.app loads  
- [ ] Feed / login / report work against Render  
- [ ] Super admin ops console  

---

## Limits (free)

- Render / Neon may sleep when idle  
- Photos on Render disk may reset on redeploy  
- No Celery on free tier (create-time AI still works)

---

## Later: paid / VPS

See [DEPLOY.md](DEPLOY.md).
