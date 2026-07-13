# ===== RailVoice deployment runbook (Phase 11) =====

This guide deploys the full stack with Docker Compose + Nginx.

## Architecture

```
Internet
   │
   ▼
 Nginx (:80/:443)
   ├─ /           → web (Next.js :3000)
   ├─ /api/       → api (Gunicorn/Uvicorn :8000)
   └─ /media/     → shared upload volume
         │
   postgres (pgvector) · redis · celery worker · celery beat
```

## 1. Prerequisites

- Linux VM / VPS (2+ vCPU, 4+ GB RAM recommended)
- Docker Engine 24+ and Docker Compose v2
- DNS A records for your domain(s) (for TLS)
- Open ports 80/443

## 2. Configure environment

```bash
cp .env.production.example .env.production
```

Edit `.env.production`:

| Variable | Required | Notes |
|----------|----------|-------|
| `POSTGRES_PASSWORD` | yes | Strong password |
| `SECRET_KEY` | yes | 32+ random chars |
| `CORS_ORIGINS` | yes | Exact web origin(s) |
| `PUBLIC_BASE_URL` | yes | Public API base (for photo URLs) |
| `NEXT_PUBLIC_API_URL` | yes | Browser API URL (bake into web image) |
| `OTP_MOCK_MODE` | must be `false` | Production blocks startup if true |
| `GOOGLE_OAUTH_MOCK_MODE` | must be `false` | Same |
| `RUN_SEED` | first boot only | Seeds stations + super admin |

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Same-host HTTP (quick smoke):**

```env
PUBLIC_BASE_URL=http://YOUR_SERVER_IP
NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP/api/v1
CORS_ORIGINS=http://YOUR_SERVER_IP
OTP_MOCK_MODE=false
GOOGLE_OAUTH_MOCK_MODE=false
```

> Tip: for first production smoke you can temporarily keep OTP mock **only on a private VM**, but the API will refuse to start with mocks when `APP_ENV=production`. Use a staging `APP_ENV=staging` + `DEBUG=true` override if you still need mock OTP.

To allow a staging deploy with mock OTP, set in `.env.production`:

```env
APP_ENV=staging
DEBUG=true
OTP_MOCK_MODE=true
GOOGLE_OAUTH_MOCK_MODE=true
```

## 3. First deploy

```bash
# From repo root
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

First boot with seed:

```env
RUN_SEED=true
```

After seed succeeds, set `RUN_SEED=false` and recreate api:

```bash
# edit .env.production → RUN_SEED=false
docker compose -f docker-compose.prod.yml --env-file .env.production up -d api
```

## 4. Verify

```bash
curl -fsS http://YOUR_HOST/health
curl -fsS http://YOUR_HOST/health/ready
curl -fsS http://YOUR_HOST/          # Next.js
curl -fsS http://YOUR_HOST/api/v1/stations?zone_code=WR
```

Super admin (after seed): OTP login with `+919999999999` only if mock OTP is enabled (staging). In real production, provision staff roles in DB after verifying a real mobile/Google user.

## 5. Enable HTTPS

1. Obtain certificates (Let's Encrypt / cloud LB).
2. Place `fullchain.pem` + `privkey.pem` in `deploy/certs/`.
3. Replace `deploy/nginx/conf.d/railvoice.conf` with `railvoice.tls.conf.example` (edit `server_name`).
4. Update `.env.production` to `https://` URLs and rebuild **web** (API URL is build-time):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build web nginx
```

## 6. Operations

| Task | Command |
|------|---------|
| Logs | `docker compose -f docker-compose.prod.yml logs -f api web nginx` |
| Migrate only | Restarted automatically via `scripts/entrypoint.sh` on api/worker start |
| Rebuild API | `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build api worker beat` |
| Backup DB | `docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U railvoice railvoice > backup.sql` |
| Restore DB | `cat backup.sql \| docker compose -f docker-compose.prod.yml exec -T postgres psql -U railvoice railvoice` |

Metrics: `GET /metrics` (Prometheus format). Restrict at Nginx in real prod.

## 7. Security checklist

- [ ] Strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- [ ] `OTP_MOCK_MODE=false`, `GOOGLE_OAUTH_MOCK_MODE=false`
- [ ] TLS certificates + HSTS
- [ ] Firewall: only 80/443 public; never expose Postgres/Redis ports
- [ ] Rotate JWT / refresh by forcing logout (revokes refresh families)
- [ ] Offsite DB + media volume backups
- [ ] Disable `/docs` in public Nginx if you do not want OpenAPI public

## 8. Rollback

```bash
# Redeploy previous image tags / git SHA
git checkout <previous-sha>
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Keep a DB dump before each migrate-heavy release.

## 9. Local production smoke (optional)

```bash
cp .env.production.example .env.production
# set POSTGRES_PASSWORD + SECRET_KEY (32+), APP_ENV=staging DEBUG=true for mocks
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Open `http://localhost` (Nginx). Dev compose remains `docker compose up` on ports 3000/8000.

## 10. What production hardens vs local compose

| Local (`docker-compose.yml`) | Prod (`docker-compose.prod.yml`) |
|------------------------------|-----------------------------------|
| Uvicorn `--reload` + bind mounts | Gunicorn workers, baked images |
| Ports 8000/3000/5432/6379 open | Only Nginx 80/443 published |
| OTP mock on | Mock blocked when production |
| Seed every start | Seed opt-in via `RUN_SEED` |
