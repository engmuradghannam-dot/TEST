# Nexus Framework - SaaS ERP Platform

[![CI/CD](https://github.com/engmuradghannam-dot/Nexus-Framework/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/engmuradghannam-dot/Nexus-Framework/actions/workflows/ci-cd.yml)

A production-ready, multi-tenant SaaS ERP platform built with Django + React, deployed on Kubernetes with full observability.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx Ingress                         │
│              (SSL Termination, Rate Limiting, WAF)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                           │
   ┌────▼────┐                 ┌────▼────┐
   │ Frontend │                 │ Backend │
   │  React   │                 │ Django  │
   │  (SPA)   │                 │  DRF    │
   └─────────┘                 └────┬────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
              │ PostgreSQL │  │  Redis    │  │  Celery   │
              │(Multi-tenant│  │  Cache    │  │  Workers  │
              │  schemas)  │  │  Queue    │  │           │
              └────────────┘  └───────────┘  └───────────┘
```

## Key Features

### Multi-Tenancy
- **django-tenants** with `TenantMixin` + `DomainMixin`
- Subdomain and custom domain routing
- Schema-per-tenant isolation
- Tenant-aware middleware with plan limit enforcement

### Plugin System
- Marketplace with reviews and ratings
- Dynamic loading with `importlib`
- Hook registry for extensibility
- Per-tenant plugin installation

### Billing & Subscriptions
- **Stripe** integration (payments, subscriptions, webhooks)
- Plans with configurable limits
- Invoice generation and payment tracking
- Usage-based billing records

### Kubernetes Deployment
- Helm charts with configurable values
- HPA for auto-scaling
- Pod Disruption Budgets
- Network Policies for security
- Secrets management

### CI/CD
- GitHub Actions pipeline
- Automated testing (backend + frontend)
- Security scanning (Trivy, Bandit, Safety)
- SBOM generation
- Staging and Production deployments

### Observability
- **Prometheus** metrics and alerting
- **Grafana** dashboards
- **Loki** log aggregation
- **Tempo** distributed tracing (OpenTelemetry)
- **Sentry** error tracking

### Security Hardening
- Rate limiting (Redis-based)
- WAF rules (ModSecurity)
- Security headers (CSP, HSTS, X-Frame-Options)
- Secrets rotation policy
- Non-root containers
- Read-only root filesystems

## Quick Start

### Local Development (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/engmuradghannam-dot/Nexus-Framework.git
cd Nexus-Framework

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate --run-syncdb
docker-compose exec backend python manage.py migrate_schemas --shared

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access the app
# Frontend: http://localhost
# Backend API: http://localhost/api/
# Admin: http://localhost/admin/
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9090
```

### Kubernetes Deployment

```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install dependencies
helm dependency build ./k8s/helm/nexus-saas

# Deploy to staging
helm upgrade --install nexus-saas-staging ./k8s/helm/nexus-saas   --namespace staging   --create-namespace   --set image.backend.tag=latest   --set image.frontend.tag=latest

# Deploy to production
helm upgrade --install nexus-saas ./k8s/helm/nexus-saas   --namespace production   --create-namespace   --set image.backend.tag=v1.0.0   --set image.frontend.tag=v1.0.0
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `false` |
| `SECRET_KEY` | Django secret key | Required |
| `DB_HOST` | PostgreSQL host | `db` |
| `DB_NAME` | Database name | `nexus` |
| `DB_USER` | Database user | `nexus` |
| `DB_PASSWORD` | Database password | `nexus` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/1` |
| `STRIPE_SECRET_KEY` | Stripe API key | - |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | - |
| `SENTRY_DSN` | Sentry DSN | - |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry endpoint | - |

## Project Structure

```
Nexus-Framework/
├── backend/              # Django backend
│   ├── apps/
│   │   ├── tenants/      # Multi-tenancy
│   │   ├── plugins/      # Plugin system
│   │   ├── billing/      # Stripe billing
│   │   ├── core/         # Core utilities
│   │   ├── accounts/     # Accounting
│   │   ├── inventory/    # Inventory
│   │   ├── buying/       # Purchasing
│   │   ├── selling/      # Sales
│   │   ├── manufacturing/# Manufacturing
│   │   ├── hr/           # Human Resources
│   │   ├── crm/          # CRM
│   │   ├── projects/     # Project Management
│   │   ├── assets/       # Fixed Assets
│   │   └── workflow/     # Workflow Engine
│   └── nexus/            # Django settings
├── frontend/             # React frontend
│   └── src/
├── k8s/                  # Kubernetes manifests
│   └── helm/
│       └── nexus-saas/   # Helm chart
├── observability/        # Monitoring stack
│   ├── prometheus/
│   ├── grafana/
│   ├── loki/
│   ├── tempo/
│   └── sentry/
├── security/             # Security policies
│   ├── policies/
│   ├── waf/
│   └── secrets/
├── .github/
│   └── workflows/        # CI/CD pipelines
├── docker-compose.yml    # Local development
└── README.md
```

## License

MIT License - see LICENSE file for details.
