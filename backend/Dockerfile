# ═══════════════════════════════════════════
# Nexus SaaS Backend - Multi-stage Build
# ═══════════════════════════════════════════

# ── Stage 1: Dependencies ──────────────────
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     libpq-dev     python3-dev     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --user --no-cache-dir -r requirements-prod.txt

# ── Stage 2: Production ───────────────────
FROM python:3.11-slim-bookworm AS production

# Security: Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus nexus

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     libpq5     postgresql-client     redis-tools     curl     && rm -rf /var/lib/apt/lists/*     && apt-get clean

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/nexus/.local
ENV PATH=/home/nexus/.local/bin:$PATH

# Copy application code
COPY --chown=nexus:nexus . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create required directories
RUN mkdir -p /tmp /app/media /app/static /app/logs &&     chown -R nexus:nexus /tmp /app/media /app/static /app/logs

USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3     CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["web"]
