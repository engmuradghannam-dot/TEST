from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
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
    path('api/health/', include('nexus.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
