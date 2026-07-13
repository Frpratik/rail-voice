#!/usr/bin/env bash
# Free-tier / Render start command
set -euo pipefail

echo "[free-boot] Ensuring pgvector extension..."
python - <<'PY'
import os
import sys
import psycopg2

url = os.environ.get("DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL", "")
if url.startswith("postgresql+asyncpg://"):
    url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
if not url:
    print("DATABASE_URL_SYNC missing", file=sys.stderr)
    sys.exit(1)

if "neon.tech" in url and "sslmode=" not in url:
    url = url + ("&" if "?" in url else "?") + "sslmode=require"

conn = psycopg2.connect(url)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
print("[free-boot] pgvector ready")
conn.close()
PY

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
