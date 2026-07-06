# Nexus Framework - Production Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Domain name (for SSL)
- Server with at least 2GB RAM

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/engmuradghannam-dot/Nexus-Framework.git
cd Nexus-Framework
cp .env.example .env
# Edit .env with your production values
```

### 2. SSL Certificates

#### Option A: Self-signed (development only)
```bash
./nginx/generate-ssl.sh
```

#### Option B: Let's Encrypt (production)
```bash
# Install certbot
certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

#### Option C: Cloudflare Origin CA
```bash
# Download from Cloudflare dashboard
cp origin_ca_rsa_root.pem nginx/ssl/cert.pem
cp origin_ca_rsa_root.key nginx/ssl/key.pem
```

### 3. Secrets Management (Production)

#### Option A: Docker Secrets (Swarm mode)
```bash
docker swarm init
docker secret create django_secret_key <(openssl rand -base64 50)
docker secret create db_password <(openssl rand -base64 32)
```

#### Option B: Environment Variables
```bash
# Edit .env
SECRET_KEY=$(openssl rand -base64 50)
DB_PASSWORD=$(openssl rand -base64 32)
```

### 4. Build and Run

```bash
# Build frontend first
docker-compose --profile build up frontend-builder

# Start all services
docker-compose up -d

# Check health
curl https://localhost/health
```

### 5. Database Setup

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Collect static files (if not using volume)
docker-compose exec backend python manage.py collectstatic --noinput
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐     ┌─────────────┐
│    Nginx    │────▶│  Rate Limit │
│   (SSL/TLS) │     │   + Cache   │
└──────┬──────┘     └─────────────┘
       │
       ├──▶ /static/* ──▶ Static Files
       ├──▶ /media/*  ──▶ Media Files
       └──▶ /api/*    ──▶ Backend (Gunicorn)
                            │
                            ├──▶ PostgreSQL
                            ├──▶ Redis
                            └──▶ Celery Worker
```

## Monitoring

### Health Checks
- Backend: `curl https://your-domain.com/api/v1/`
- Nginx: `curl https://your-domain.com/health`
- Database: `docker-compose exec db pg_isready -U postgres`

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

### Performance
```bash
# Check resource usage
docker stats

# Database connections
docker-compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

## Backup

### Database
```bash
# Backup
docker-compose exec db pg_dump -U postgres nexus > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T db psql -U postgres nexus < backup_20240101.sql
```

### Media Files
```bash
# Backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz ./backend/media

# Restore
tar -xzf media_backup_20240101.tar.gz -C ./backend/
```

## Scaling

### Horizontal Scaling
```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale workers
docker-compose up -d --scale worker=5
```

### Vertical Scaling
- Increase `worker_processes` in nginx.conf
- Increase Gunicorn workers: `--workers $(($(nproc) * 2 + 1))`
- Increase Celery concurrency: `--concurrency=4`

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   - Check cert/key permissions: `chmod 600 nginx/ssl/*`
   - Verify cert validity: `openssl x509 -in nginx/ssl/cert.pem -text -noout`

2. **Database Connection Failed**
   - Check if DB is healthy: `docker-compose ps db`
   - Verify connection string in .env

3. **Static Files 404**
   - Run collectstatic: `docker-compose exec backend python manage.py collectstatic`
   - Check volume mount: `docker-compose exec nginx ls /var/www/static`

4. **Celery Worker Not Processing**
   - Check worker logs: `docker-compose logs worker`
   - Verify Redis connection: `docker-compose exec redis redis-cli ping`

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database password
- [ ] Enable HTTPS only (no HTTP)
- [ ] Configure firewall (ufw/iptables)
- [ ] Disable DEBUG mode
- [ ] Set up Sentry for error tracking
- [ ] Enable database backups
- [ ] Configure log rotation
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Regular security updates
