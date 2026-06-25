# Dockerfile
# Multi-stage build for Intelligent DSS Backend

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — install dependencies
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies needed to compile some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install only production dependencies
# requirements-dev.txt is NOT copied — keeps the image lean
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Final image — lean runtime
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --gid 1001 appuser

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create runtime directories and set ownership
RUN mkdir -p logs reports && \
    chown -R appuser:appuser /app

# Make entrypoint executable
RUN chmod +x scripts/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Health check using the Python script (doesn't need curl to be in PATH)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/healthcheck.py

EXPOSE 8000

ENTRYPOINT ["scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]