# ───────────────────────────────────────────
# Nexus SaaS Backend - Multi-stage Build
# ───────────────────────────────────────────

# Stage 1: Build dependencies
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     libpq-dev     python3-dev     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --user --no-cache-dir -r requirements-prod.txt

# Stage 2: Production image
FROM python:3.11-slim-bookworm AS production

# Security: Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus nexus

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     libpq5     curl     && rm -rf /var/lib/apt/lists/*     && apt-get clean

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/nexus/.local
ENV PATH=/home/nexus/.local/bin:$PATH

# Copy application code
COPY --chown=nexus:nexus . .

# Security: Set proper permissions
RUN chmod -R 755 /app &&     chmod -R 644 /app/**/*.py &&     chmod +x /app/entrypoint.sh

# Security: Read-only root filesystem
RUN mkdir -p /tmp /app/media /app/static &&     chown -R nexus:nexus /tmp /app/media /app/static

USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3     CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "nexus.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "--enable-stdio-inheritance"]
