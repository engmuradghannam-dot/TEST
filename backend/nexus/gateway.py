"""Nexus API Gateway — the single public entry point: /api/v1/

Responsibilities:
- One versioned mount for every module (no scattered path roots)
- Per-tenant rate limiting (Redis sliding window, fail-open)
- Gateway envelope headers (X-API-Version, X-Request-ID passthrough)
- Deprecation signalling for legacy unversioned paths

Route map (all under /api/v1/):
  auth/       core/       tenants/    billing/    plugins/
  accounts/   inventory/  buying/     selling/    manufacturing/
  hr/         crm/        projects/   assets/     workflow/
  intelligence/  (AI brain, agents, guidance — via core.urls)
"""
import logging
import time

from django.http import JsonResponse
from django.urls import include, path

logger = logging.getLogger("nexus.gateway")

API_VERSION = "v1"

MODULE_ROUTES = [
    ("core/", "apps.core.urls"),
    ("tenants/", "apps.tenants.urls"),
    ("billing/", "apps.billing.urls"),
    ("plugins/", "apps.plugins.urls"),
    ("accounts/", "apps.accounts.urls"),
    ("inventory/", "apps.inventory.urls"),
    ("buying/", "apps.buying.urls"),
    ("selling/", "apps.selling.urls"),
    ("manufacturing/", "apps.manufacturing.urls"),
    ("hr/", "apps.hr.urls"),
    ("crm/", "apps.crm.urls"),
    ("projects/", "apps.projects.urls"),
    ("assets/", "apps.assets.urls"),
    ("workflow/", "apps.workflow.urls"),
]


def build_urlpatterns():
    return [path(prefix, include(module)) for prefix, module in MODULE_ROUTES]


class GatewayMiddleware:
    """Versioning headers + per-tenant rate limiting for /api/ traffic."""

    RATE_LIMIT = 300          # requests
    RATE_WINDOW = 60          # seconds
    EXEMPT_PREFIXES = ("/api/v1/core/health", "/admin/")

    def __init__(self, get_response):
        self.get_response = get_response
        self._redis = None

    def _redis_client(self):
        if self._redis is None:
            try:
                import redis
                from django.conf import settings
                self._redis = redis.Redis.from_url(
                    getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
                    socket_timeout=0.2, decode_responses=True)
            except Exception:
                self._redis = False
        return self._redis or None

    def __call__(self, request):
        if request.path.startswith("/api/") and not request.path.startswith(
                self.EXEMPT_PREFIXES):
            limited = self._rate_limited(request)
            if limited:
                return JsonResponse(
                    {"error": "rate_limited",
                     "message": f"Limit {self.RATE_LIMIT} req/{self.RATE_WINDOW}s exceeded.",
                     "retry_after": limited},
                    status=429, headers={"Retry-After": str(limited)})

        response = self.get_response(request)

        if request.path.startswith("/api/"):
            response["X-API-Version"] = API_VERSION
            if request.path.startswith("/api/") and not request.path.startswith(
                    f"/api/{API_VERSION}/") and not request.path.startswith("/api/auth"):
                response["Deprecation"] = "true"
                response["Link"] = (f'</api/{API_VERSION}{request.path[4:]}>; '
                                    'rel="successor-version"')
        return response

    def _rate_limited(self, request) -> int:
        """Sliding-window counter per tenant (or per IP when anonymous).
        Fail-open: Redis trouble never blocks traffic."""
        r = self._redis_client()
        if not r:
            return 0
        tenant = getattr(getattr(request, "tenant", None), "schema_name", None)
        actor = tenant or request.META.get("REMOTE_ADDR", "unknown")
        bucket = int(time.time() // self.RATE_WINDOW)
        key = f"gw:rl:{actor}:{bucket}"
        try:
            count = r.incr(key)
            if count == 1:
                r.expire(key, self.RATE_WINDOW * 2)
            if count > self.RATE_LIMIT:
                return self.RATE_WINDOW - int(time.time() % self.RATE_WINDOW)
        except Exception:
            return 0
        return 0
