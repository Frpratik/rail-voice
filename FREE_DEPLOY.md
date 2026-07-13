# Free deployment (no paid server needed)

Best free combo for RailVoice:

| Layer | Service | Cost |
|-------|---------|------|
| Frontend | [Vercel](https://vercel.com) | Free |
| API | [Render](https://render.com) Web Service | Free (spins down after ~15 min idle) |
| Postgres + pgvector | [Neon](https://neon.tech) | Free |
| Redis / Celery | Skipped | N/A — AI already runs sync on create |

Cold start: first request to Render after idle can take 30–60s. That’s normal on free.

---

## 0. Push code to GitHub

If the repo isn’t on GitHub yet:

```bash
git remote -v
# create a private/public repo, then:
git add -A
git commit -m "Prep free-tier deploy"
git push -u origin main
```

You need a GitHub repo for Vercel + Render to build from.

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
2. **New → Web Service** → select the RailVoice repo  
3. Settings:

| Field | Value |
|-------|--------|
| Root Directory | `railvoice-backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `bash scripts/free_boot.sh` |
| Instance type | **Free** |

4. Environment variables (Environment tab):

| Key | Value |
|-----|--------|
| `APP_ENV` | `staging` |
| `DEBUG` | `false` |
| `SECRET_KEY` | long random string (32+) |
| `DATABASE_URL` | Neon async URL (`postgresql+asyncpg://...?ssl=require`) |
| `DATABASE_URL_SYNC` | Neon sync URL (`postgresql://...?sslmode=require`) |
| `CELERY_ENABLED` | `false` |
| `OTP_MOCK_MODE` | `true` |
| `OTP_MOCK_CODE` | `123456` |
| `GOOGLE_OAUTH_MOCK_MODE` | `true` |
| `RUN_SEED` | `true` |
| `CORS_ORIGINS` | `https://YOUR-VERCEL-URL.vercel.app` (update after step 3) |
| `PUBLIC_BASE_URL` | `https://YOUR-RENDER-SERVICE.onrender.com` |
| `LOCAL_STORAGE_PATH` | `storage/uploads` |

5. Deploy → wait until live.  
6. Test:

```bash
curl https://YOUR-RENDER-SERVICE.onrender.com/health
curl https://YOUR-RENDER-SERVICE.onrender.com/health/ready
```

Super admin (seeded): mobile `+919999999999`, OTP `123456`.

---

## 3. Vercel (frontend) — ~3 minutes

1. Sign up: https://vercel.com → Import GitHub repo  
2. Settings:

| Field | Value |
|-------|--------|
| Root Directory | `railvoice-web` |
| Framework | Next.js |

3. Environment variable:

| Key | Value |
|-----|--------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RENDER-SERVICE.onrender.com/api/v1` |

4. Deploy.  
5. Copy the Vercel URL (e.g. `https://railvoice-xxx.vercel.app`).

---

## 4. Wire CORS (important)

Back on **Render → Environment**:

```text
CORS_ORIGINS=https://railvoice-xxx.vercel.app
PUBLIC_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

**Manual Redeploy** the API so CORS updates. Then hard-refresh the Vercel site.

---

## 5. Smoke test checklist

- [ ] Open Vercel URL → home feed loads (may be slow on first hit)  
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
