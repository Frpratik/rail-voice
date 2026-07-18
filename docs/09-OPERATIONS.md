# 9. Operations Runbook

## 9.1 Service map

| Check | Command / URL |
|-------|----------------|
| API alive | `GET https://rail-voice.onrender.com/health` |
| DB ready | `GET https://rail-voice.onrender.com/health/ready` |
| Stations | `GET …/api/v1/stations?zone_code=WR` |
| Web | `GET https://rail-voice.vercel.app` |
| OpenAPI | https://rail-voice.onrender.com/docs |

## 9.2 Common incidents

### Frontend loads but no data

1. Confirm Vercel build embeds `/api/v1` not `localhost:8000` (view source / network).  
2. Redeploy Vercel without cache; set `NEXT_PUBLIC_API_URL=/api/v1`.  
3. Confirm Render is awake (`/health`).  
4. Check browser Network for CORS / 502 from proxy.

### API 502 / timeout on first request

Render free spin-down. Wait and retry; expect cold start.

### `/health/ready` fails

Neon suspended or bad `DATABASE_URL(_SYNC)`. Verify SSL params; wake Neon console.

### Migrations missing

Ensure start uses `scripts/free_boot.sh` or `entrypoint.sh`, not bare uvicorn without migrate.

### Admin 403

User lacks official role. Login as seeded `+919999999999` / OTP `123456` (mock), or insert `user_roles`.

### Photos missing after redeploy

Expected on free Render ephemeral disk. Move to S3 in later phase.

## 9.3 Access credentials (staging)

| Account | How |
|---------|-----|
| Super admin | OTP `+919999999999` / `123456` |
| Passenger | Any `+91` + mock OTP |
| Google | Continue with Google (mock) on login |

**Rotate Neon passwords** if ever pasted into chat or tickets.

## 9.4 Deploy / rollback

```bash
# Ship
git push origin main
# Render & Vercel auto-deploy (or Manual Deploy)

# Rollback
# Redeploy previous Git SHA in Render/Vercel dashboards
# Restore Neon from backup if schema-breaking (none automated on free)
```

## 9.5 Logs

- Render → service → Logs  
- Vercel → deployment → Functions / build logs  
- Correlation: response header `X-Correlation-Id`

## 9.6 Metrics

`GET /metrics` — Prometheus text. Scrape example: `deploy/prometheus/prometheus.yml.example`. Restrict in hardened prod.

## 9.7 Seed & data

```bash
# Inside API container / boot
alembic upgrade head
python -m app.scripts.seed
```

`RUN_SEED=true` on first boot; set `false` after to avoid repeated work (seed is mostly idempotent).

## 9.8 On-call checklist (minimal)

- [ ] `/health` and `/health/ready`  
- [ ] Vercel homepage + network calls to `/api/v1/stations`  
- [ ] One OTP login  
- [ ] One admin dashboard load with super admin  
- [ ] Recent Render/Vercel deploy success
