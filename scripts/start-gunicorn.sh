#!/usr/bin/env bash
set -euo pipefail

exec gunicorn \
  --bind "${GUNICORN_BIND:-0.0.0.0:${PORT:-__PORT__}}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --worker-class "${GUNICORN_WORKER_CLASS:-sync}" \
  --threads "${GUNICORN_THREADS:-1}" \
  --worker-tmp-dir "${GUNICORN_WORKER_TMP_DIR:-/dev/shm}" \
  --keep-alive "${GUNICORN_KEEPALIVE:-5}" \
  --timeout "${GUNICORN_TIMEOUT:-30}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
  --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
  --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-100}" \
  --access-logfile "-" \
  --error-logfile "-" \
  config.wsgi:application
