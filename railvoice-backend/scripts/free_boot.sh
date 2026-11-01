#!/usr/bin/env bash
# Free-tier / Render start command
set -euo pipefail

echo "[free-boot] Migrations..."
alembic upgrade head

if [ "${RUN_SEED:-true}" = "true" ]; then
  echo "[free-boot] Seeding..."
  python -m app.scripts.seed || true
fi

PORT="${PORT:-8000}"
echo "[free-boot] Starting API on :${PORT}"
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -b "0.0.0.0:${PORT}" \
  -w "${WEB_CONCURRENCY:-1}" \
  --timeout 120
