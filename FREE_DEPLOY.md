# Free deployment (no paid server needed)

Best free combo for RailVoice:

| Layer | Service | Cost |
|-------|---------|------|
| Frontend | [Vercel](https://vercel.com) | Free |
| API | [Render](https://render.com) Web Service | Free (spins down after ~15 min idle) |
| Postgres + pgvector | [Neon](https://neon.tech) | Free |
| Redis / Celery | Skipped | N/A — AI already runs sync on create |

Cold start: first request to Render after idle can take 30–60s. That’s normal on free.

### Your live frontend

```text
https://rail-voice.vercel.app
```

---

## 0. Push code to GitHub

Repo: https://github.com/Frpratik/rail-voice

Already pushed — skip if `main` is up to date.

---

## 1. Neon (database) — ~2 minutes

1. Sign up: https://console.neon.tech  
2. Create project → region close to you (e.g. Singapore / Mumbai if available)  
3. Open **SQL Editor**, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

4. **Dashboard → Connection details** → copy connection string.  
5. Make two variants:

```text
# Sync (psycopg2 / Alembic) — usually already looks like this:
postgresql://USER:PASSWORD@HOST/neondb?sslmode=require

# Async (FastAPI) — change scheme + ssl param:
postgresql+asyncpg://USER:PASSWORD@HOST/neondb?ssl=require
```

Keep these handy for Render env vars.

---

## 2. Render (API) — ~5 minutes

1. Sign up with GitHub: https://dashboard.render.com  
2. **New → Web Service** → select **Frpratik/rail-voice**  
3. Settings:

| Field | Value |
|-------|--------|
| Root Directory | `railvoice-backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `bash scripts/free_boot.sh` |
| Instance type | **Free** |

4. Environment variables (Environment tab) — **copy/paste**:

| Key | Value |
|-----|--------|
| `APP_ENV` | `staging` |
| `DEBUG` | `false` |
| `SECRET_KEY` | *(generate a long random 32+ string)* |
| `DATABASE_URL` | Neon async URL (`postgresql+asyncpg://...?ssl=require`) |
| `DATABASE_URL_SYNC` | Neon sync URL (`postgresql://...?sslmode=require`) |
| `CELERY_ENABLED` | `false` |
| `OTP_MOCK_MODE` | `true` |
| `OTP_MOCK_CODE` | `123456` |
| `GOOGLE_OAUTH_MOCK_MODE` | `true` |
| `RUN_SEED` | `true` |
| `CORS_ORIGINS` | `https://rail-voice.vercel.app,http://localhost:3000` |
| `PUBLIC_BASE_URL` | `https://YOUR-RENDER-SERVICE.onrender.com` |
| `LOCAL_STORAGE_PATH` | `storage/uploads` |

Copy-paste for CORS (ready now):

```text
https://rail-voice.vercel.app,http://localhost:3000
```

5. Deploy → wait until live. Note your API URL, e.g. `https://rail-voice-api.onrender.com`.  
6. Update `PUBLIC_BASE_URL` to that URL, then **Manual Deploy**.  
7. Test:

```bash
curl https://YOUR-RENDER-SERVICE.onrender.com/health
curl https://YOUR-RENDER-SERVICE.onrender.com/health/ready
```

Super admin (seeded): mobile `+919999999999`, OTP `123456`.

---

## 3. Vercel (frontend) — already live

Your app: **https://rail-voice.vercel.app**

Root Directory: `railvoice-web`

### Environment variable (Vercel → Settings → Environment Variables)

| Key | Value (after Render is live) |
|-----|------------------------------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RENDER-SERVICE.onrender.com/api/v1` |

Example once you know the Render hostname:

```text
NEXT_PUBLIC_API_URL=https://rail-voice-api.onrender.com/api/v1
```

Redeploy the Vercel project after setting this (Deployments → … → Redeploy).

---

## 4. Wire CORS on Render (copy/paste)

**Render → Environment** — set exactly:

```text
CORS_ORIGINS=https://rail-voice.vercel.app,http://localhost:3000
PUBLIC_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

Replace `YOUR-RENDER-SERVICE` with your real Render hostname, then **Manual Redeploy** the API.

Open https://rail-voice.vercel.app and hard-refresh.

---

## 5. Smoke test checklist

- [ ] https://rail-voice.vercel.app → home feed loads (may be slow on first hit)  
- [ ] `/login` → OTP `+919876543210` / `123456`  
- [ ] Report an issue with photos  
- [ ] Super admin `+919999999999` → Profile → Operations console  

---

## Limits to expect (free)

- Render sleeps → first request after idle is slow  
- Ephemeral disk → uploaded photos may disappear on redeploy (OK for demo)  
- No Celery beat → no scheduled priority recalcs (create-time AI still works)  
- Neon free compute suspends → first DB query after idle can be slow  

---

## Optional: skip Redis completely

Already done when `CELERY_ENABLED=false`. Rate limiting uses in-memory buckets (per instance).

---

## When you later want “real” hosting

Use [DEPLOY.md](DEPLOY.md) + a cheap VPS (`docker-compose.prod.yml`) with TLS.
