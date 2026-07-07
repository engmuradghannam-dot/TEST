# Nexus — Cognitive ERP Platform

[![Tests](https://img.shields.io/badge/tests-118%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![Django](https://img.shields.io/badge/django-4.2-green)]()
[![React](https://img.shields.io/badge/react-18-blue)]()

The first Arabic-first, AI-native, multi-tenant SaaS ERP — built for the Gulf SME market.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx Ingress + WAF                          │
│             SSL Termination · Rate Limiting · CORS              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
       ┌────▼────┐                   ┌────▼────────┐
       │ React   │                   │ Django DRF  │
       │ (SPA)   │                   │ /api/v1/    │◄── API Gateway
       └─────────┘                   └─────────────┘    (versioned,
                                           │             rate-limited)
                    ┌──────────────────────┼───────────────────┐
                    │                      │                   │
              ┌─────▼──────┐        ┌──────▼─────┐    ┌───────▼──────┐
              │ PostgreSQL │        │   Redis    │    │    Celery    │
              │ per-tenant │        │ Event Bus  │    │   Workers    │
              │  schemas   │        │  + Cache   │    │  + Scheduler │
              └────────────┘        └────────────┘    └──────────────┘
```

---

## Core Capabilities

### ERP Modules (14)
| Module | Capabilities |
|--------|-------------|
| **Accounting** | Double-entry GL, COA, fiscal years/periods, year-end closing, multi-currency |
| **Sales** | SO, invoicing, VAT (ZATCA Phase 2 clearance/reporting), delivery |
| **Purchasing** | PO, three-way matching, supplier management |
| **Inventory** | Stock entries, serial/batch, warehouse management, reorder |
| **Manufacturing** | BOM, work orders, production tracking |
| **HR & Payroll** | Employees, departments, leave, payroll (GOSI-aware) |
| **CRM** | Leads, opportunities, pipeline |
| **Projects (PMO)** | Full PMO: tasks, milestones, risks, issues, Gantt, Kanban |
| **Assets** | Fixed assets, depreciation, asset categories |
| **Billing** | Subscription plans, Stripe integration, tenant quotas |
| **Compliance** | SOC 2, ISO 27001, ISO 9001, GDPR — automated control checks |
| **KPIs** | Company KPIs, dashboards, history tracking |
| **Industries** | Industry-specific control libraries |
| **Market** | Country localizations, partner directory, app marketplace |

### AI Engine (Cognitive Layer)
- **Multi-Provider LLM** — Claude, GPT-4o, Gemini, Groq with automatic fallback
- **Natural-Language ERP** — "اعمل تقرير الربحية للربع الثاني" → resolves to report
- **AI Agents** — Finance, HR, Supply Chain, Admin agents with sanctioned execution
- **Predictive Intelligence** — Sales forecast, demand forecast, project risk, asset failure
- **Knowledge Graph** — Entity relationships + impact analysis (what does this delay affect?)
- **Decision Engine** — Explainable rule-based routing (PO approval thresholds, etc.)
- **Self-Improvement** — Monitors own metrics → proposes improvements → human approval required

### Security (Enterprise-Grade)
- **Zero Trust** — User + Device + Location + Behavior scored on every request
- **IAM** — OIDC/OAuth2, SAML 2.0, LDAP/Active Directory with JIT provisioning
- **PAM** — Time-boxed privilege escalation with approval workflow
- **Immutable Audit** — Hash-chained, HMAC-signed append-only ledger (blockchain-style)
- **AI Security** — Anomaly detection, fraud detection, insider threat monitoring
- **Role Mining** — Automatic suggestion of roles from permission usage patterns

### Multi-Tenancy
- Schema-per-tenant isolation (django-tenants)
- CompanyScopedMixin on all ViewSets (row-level security)
- Branch-level RLS (BranchScopedMixin)
- Per-tenant rate limiting in the API Gateway

---

## Getting Started

### Prerequisites
- Python 3.12, Node 20, PostgreSQL 16, Redis 7

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in DB_*, REDIS_URL, SECRET_KEY
python manage.py migrate
python manage.py seed_localization    # currencies + Gulf tax rules
python manage.py seed_compliance      # SOC2/ISO27001/ISO9001/GDPR controls
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### Self-Service Onboarding
```bash
# Register a new company
POST /api/v1/tenants/onboarding/register/
{ "company_name": "My Co", "admin_email": "admin@myco.com",
  "admin_password": "...", "country": "SA", "vat_number": "300..." }

# Run setup wizard (COA, warehouse, currencies, compliance)
POST /api/v1/tenants/onboarding/setup/

# Check readiness
GET /api/v1/tenants/onboarding/status/
```

---

## API Reference

Swagger UI: `GET /api/v1/docs/`  
OpenAPI schema: `GET /api/v1/schema/`  
ReDoc: `GET /api/v1/redoc/`

All API routes under `/api/v1/{module}/`.

---

## Tests

```bash
cd backend
pytest tests/ tests/integration/ tests/e2e/  # 118 tests, real PostgreSQL
```

Coverage areas: financial core (double-entry, fiscal, ZATCA), enterprise security
(IAM, audit chain, PAM, role mining), AI (forecasting, decisions, knowledge graph),
compliance, onboarding, all 14 ERP modules, E2E workflows.

---

## Deployment

Kubernetes manifests: `k8s/`  
Helm chart with HPA, PDB, Network Policies, multi-region support.

Observability stack: Grafana + Prometheus + Loki + Tempo + Sentry  
CI/CD: GitHub Actions (`.github/workflows/`)

---

## Localization

Gulf countries supported out-of-the-box:

| Country | VAT | E-Invoicing | Standard |
|---------|-----|-------------|----------|
| 🇸🇦 Saudi Arabia | 15% | ZATCA Phase 2 | IFRS |
| 🇦🇪 UAE | 5% | Peppol/custom | IFRS |
| 🇧🇭 Bahrain | 10% | — | IFRS |
| 🇴🇲 Oman | 5% | — | IFRS |
| 🇶🇦 Qatar | 0% | — | IFRS |
| 🇰🇼 Kuwait | 0% | — | IFRS |
| 🇯🇴 Jordan | 16% | — | IFRS |
| 🇪🇬 Egypt | 14% | — | EAS |

---

## License

Proprietary — All rights reserved. © Murad Ghannam
