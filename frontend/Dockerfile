# ═══════════════════════════════════════════
# Nexus SaaS Frontend - Multi-stage Build
# ═══════════════════════════════════════════

# ── Stage 1: Build ────────────────────────
FROM node:20-alpine AS builder

WORKDIR /build

# Install dependencies first (for caching)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Production (Nginx) ──────────
FROM nginx:alpine AS production

# Security: Create non-root user
RUN addgroup -g 1001 -S nexus &&     adduser -S nexus -u 1001

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built assets
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Security: Remove default server tokens
RUN sed -i 's/server_tokens on/server_tokens off/' /etc/nginx/nginx.conf

# Set proper permissions
RUN chown -R nexus:nexus /usr/share/nginx/html &&     chown -R nexus:nexus /var/cache/nginx &&     chown -R nexus:nexus /var/log/nginx &&     chown -R nexus:nexus /etc/nginx/conf.d &&     touch /var/run/nginx.pid &&     chown -R nexus:nexus /var/run/nginx.pid

USER nexus

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3     CMD curl -f http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
