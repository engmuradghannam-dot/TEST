from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tenants', views.TenantViewSet, basename='tenant')
router.register(r'domains', views.DomainViewSet, basename='domain')
router.register(r'memberships', views.TenantMembershipViewSet, basename='membership')
router.register(r'settings', views.TenantSettingsViewSet, basename='settings')

urlpatterns = [
    path('', include(router.urls)),
]
