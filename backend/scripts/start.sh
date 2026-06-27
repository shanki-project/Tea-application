#!/usr/bin/env bash
# Container entrypoint: apply DB migrations, then launch the API server.
set -euo pipefail

echo "[start] Running database migrations..."
alembic upgrade head

echo "[start] Starting Gunicorn (Uvicorn workers)..."
exec gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT:-8000}" \
  --access-logfile - \
  --error-logfile -
