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

from django.urls import path
from apps.tenants.onboarding_views import (
    RegisterView, SetupView, ImportDataView,
    OnboardingStatusView, ZATCAView)

urlpatterns += [
    path('onboarding/register/', RegisterView.as_view()),
    path('onboarding/setup/', SetupView.as_view()),
    path('onboarding/import-data/', ImportDataView.as_view()),
    path('onboarding/status/', OnboardingStatusView.as_view()),
    path('onboarding/zatca/', ZATCAView.as_view()),
]
