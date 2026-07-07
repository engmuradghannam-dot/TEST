"""Root URL configuration.

All API traffic enters through the gateway at /api/v1/ (see nexus.gateway).
Legacy unversioned paths remain mounted for backward compatibility and
answer with Deprecation headers; remove them once clients migrate.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from nexus.gateway import build_urlpatterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ── API Gateway: the single public entry point ──────────────
    path('api/v1/', include((build_urlpatterns(), 'v1'))),
    path('api/v1/auth/', include('rest_framework.urls')),
    path('api/v1/', include('nexus.api_urls')),   # main DRF router + token auth

    # ── Legacy mounts (deprecated — Deprecation header attached) ─
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/billing/', include('apps.billing.urls')),
    path('api/plugins/', include('apps.plugins.urls')),
    path('api/core/', include('apps.core.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/buying/', include('apps.buying.urls')),
    path('api/selling/', include('apps.selling.urls')),
    path('api/manufacturing/', include('apps.manufacturing.urls')),
    path('api/hr/', include('apps.hr.urls')),
    path('api/crm/', include('apps.crm.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/assets/', include('apps.assets.urls')),
    path('api/workflow/', include('apps.workflow.urls')),
    path('api/industries/', include('apps.industries.urls')),
    path('api/compliance/', include('apps.compliance.urls')),
    path('api/kpi/', include('apps.kpi.urls')),
    path('api/iam/', include('apps.iam.urls')),
    path('api/events/', include('apps.events.urls')),
    path('api/health/', include('nexus.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
