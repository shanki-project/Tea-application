# syntax=docker/dockerfile:1
# Build context is the REPO ROOT (see docker-compose.yml) so we can copy both
# the backend and the static frontend (public/).
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STATIC_DIR=/app/public \
    UPLOAD_DIR=/app/uploads \
    PORT=8000

WORKDIR /app

# System deps (build tools only needed if a wheel must compile; kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Application code
COPY backend/ /app/
# Static frontend served by FastAPI at "/"
COPY public/ /app/public/

RUN chmod +x /app/scripts/start.sh \
    && adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app
# A named volume mounted at /app/uploads inherits this ownership on first creation,
# so the non-root app user can write uploaded images.
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/api/health" || exit 1

CMD ["/app/scripts/start.sh"]
