# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Build
RUN npm run build

# Production stage - just copy static files
FROM alpine:latest AS production

WORKDIR /app

# Copy built files from builder
COPY --from=builder /app/dist /app/dist

# Copy to shared volume on start
CMD ["sh", "-c", "cp -r /app/dist/* /var/www/static/"]
