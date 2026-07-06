# Core — Modular Boundaries

`apps/core` is split into explicit boundaries to prevent a God Object:

```
core/
├── intelligence/     AI Brain, Agents, Guidance, Self-Improvement, Action Broker
│                     → PROPOSES actions. Never mutates domain state directly.
├── runtime/          Event Bus, State Machine, Observability
│                     → Infrastructure. MUST NOT import from intelligence/.
├── models.py         Shared domain models (User, Company, Branch, AuditLog…)
├── mixins.py         CompanyScopedMixin (tenant isolation)
└── *.py (root)       Views, serializers, permissions, urls
```

## Dependency direction (enforced by review)
```
intelligence ──► runtime ──► django/redis
     │
     └────────► action_broker ──► domain executors (registered by apps)
```

## Isolation layer
Intelligence and plugins interact with the domain ONLY through
`intelligence/action_broker.py`:

1. Agent/plugin emits `ProposedAction(action_type, payload, tenant_id, risk)`
2. Broker validates: executor exists, tenant scoped, risk tier policy
   - READ/LOW  → executed, audited
   - MEDIUM    → requires acting user with an allowed role
   - HIGH      → parked until human `broker.approve(action_id, approver)`
3. Every outcome is written to AuditLog and emitted on the event bus.

Domain apps register executors:
```python
from apps.core.intelligence.action_broker import broker, RiskTier

@broker.register("inventory.adjust_stock", risk=RiskTier.HIGH)
def adjust_stock(action):
    ...
```

## API Gateway
All public API traffic enters at `/api/v1/` (see `nexus/gateway.py`):
single route map, per-tenant rate limiting, version headers.
Legacy unversioned paths answer with `Deprecation: true`.
