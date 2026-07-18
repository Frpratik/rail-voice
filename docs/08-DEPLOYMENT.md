# 8. Deployment

## 8.1 Current free production (baseline)

| Layer | Provider | URL / note |
|-------|----------|------------|
| Frontend | Vercel | https://rail-voice.vercel.app |
| API | Render (Docker/Python) | https://rail-voice.onrender.com |
| Database | Neon Postgres + pgvector | Pooled connection string |
| Redis / Celery | Disabled | `CELERY_ENABLED=false` |
| Source | GitHub | https://github.com/Frpratik/rail-voice |

Step-by-step: root [`FREE_DEPLOY.md`](../FREE_DEPLOY.md).

### Critical Render settings

| Setting | Value |
|---------|--------|
| Root Directory | `railvoice-backend` |
| Build | `pip install -r requirements.txt` (or Docker) |
| Start | `bash scripts/free_boot.sh` (or Docker CMD) |
| Health check | `/health` |
| `PYTHON_VERSION` | `3.12.8` |
| `APP_ENV` | `staging` (allows mock OTP) |

`free_boot.sh`: enable `vector` → `alembic upgrade head` → seed → gunicorn on `$PORT`.

### Critical Vercel settings

| Setting | Value |
|---------|--------|
| Root Directory | `railvoice-web` |
| `NEXT_PUBLIC_API_URL` | `/api/v1` (recommended) |
| `API_PROXY_TARGET` | `https://rail-voice.onrender.com` |

Redeploy **without build cache** after changing `NEXT_PUBLIC_*`.

### Neon

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Use async URL (`postgresql+asyncpg://…?ssl=require`) and sync URL (`postgresql://…?sslmode=require`). Prefer dropping `channel_binding=require` for asyncpg compatibility.

## 8.2 Local development

```bash
cp railvoice-backend/.env.example railvoice-backend/.env
docker compose up --build
```

| Service | Port |
|---------|------|
| API | 8000 |
| Postgres | 5432 |
| Redis | 6379 |
| Web (separate) | `cd railvoice-web && npm run dev` → 3000 |

## 8.3 VPS / hardened production

See [`DEPLOY.md`](../DEPLOY.md) and `docker-compose.prod.yml`:

- Nginx reverse proxy (HTTP default; TLS example provided)  
- Gunicorn API, Celery worker + beat  
- Named volumes for media  
- `APP_ENV=production` blocks mock auth  

## 8.4 CI

`.github/workflows/ci.yml`:

- Backend: migrate, seed, pytest with coverage gate (≥55%)  
- Frontend: `npm ci`, build, lint  

## 8.5 Environment variable checklist (API)

Minimum for free staging:

```
APP_ENV=staging
DEBUG=false
SECRET_KEY=<32+ random>
DATABASE_URL=postgresql+asyncpg://...
DATABASE_URL_SYNC=postgresql://...
CELERY_ENABLED=false
OTP_MOCK_MODE=true
GOOGLE_OAUTH_MOCK_MODE=true
RUN_SEED=true
CORS_ORIGINS=https://rail-voice.vercel.app,http://localhost:3000
PUBLIC_BASE_URL=https://rail-voice.onrender.com
```

Template: `deploy/render.env.example`, `.env.free.example`.

## 8.6 Known free-tier limitations

- Render/Neon cold starts (30–60s+)  
- Ephemeral disk → photos may vanish on redeploy  
- No scheduled Celery recalcs  
- Public `/docs` and `/metrics`  
- Mock OTP not suitable for real users
