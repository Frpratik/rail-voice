#!/bin/sh
set -e

echo "[entrypoint] Waiting for database..."
python - <<'PY'
import os, time, sys
import psycopg2

url = os.environ.get("DATABASE_URL_SYNC", "")
# postgresql://user:pass@host:port/db
for i in range(60):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print("[entrypoint] Database is ready")
        sys.exit(0)
    except Exception as exc:
        print(f"[entrypoint] DB not ready ({i+1}/60): {exc}")
        time.sleep(2)
print("[entrypoint] Database wait timed out", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] Running migrations..."
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "[entrypoint] Seeding reference data..."
  python -m app.scripts.seed
fi

echo "[entrypoint] Starting: $*"
exec "$@"
