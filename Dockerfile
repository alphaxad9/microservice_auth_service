# =========================
# Stage 1 — Builder
# =========================
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build dependencies only
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# =========================
# Stage 2 — Runtime
# =========================
FROM python:3.10-slim

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/django/.local/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=my_backend.settings \
    UVICORN_WORKERS=4

WORKDIR /app

# Runtime dependencies ONLY
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /root/.local /home/django/.local

# Copy entrypoint script first (for better caching)
COPY --chown=django:django entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy project code
COPY --chown=django:django . .

RUN mkdir -p /app/staticfiles /app/media \
 && chown -R django:django /app

# Switch to non-root user
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

# Use entrypoint script (runs migrations + collectstatic at runtime)
ENTRYPOINT ["/entrypoint.sh"]

# Production-ready uvicorn with multiple workers
CMD uvicorn my_backend.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${UVICORN_WORKERS} \
    --loop asyncio \
    --http httptools