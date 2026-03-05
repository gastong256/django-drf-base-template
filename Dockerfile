# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12

# ── builder ───────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir uv==0.4.*

COPY pyproject.toml .
# Sync only production deps (no dev extras)
RUN uv sync --no-dev --no-install-project

# ── runtime ───────────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY --from=builder /build/.venv .venv

COPY apps/ apps/
COPY config/ config/
COPY scripts/start-gunicorn.sh scripts/start-gunicorn.sh
COPY manage.py .

RUN chmod +x scripts/start-gunicorn.sh \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE __PORT__

CMD ["./scripts/start-gunicorn.sh"]
