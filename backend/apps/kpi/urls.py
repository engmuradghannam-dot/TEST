from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KPIDefinitionViewSet, CompanyKPIViewSet,
    KPIHistoryViewSet, DashboardWidgetViewSet
)

router = DefaultRouter()
router.register(r'definitions', KPIDefinitionViewSet, basename='kpi-definition')
router.register(r'company-kpis', CompanyKPIViewSet, basename='company-kpi')
router.register(r'history', KPIHistoryViewSet, basename='kpi-history')
router.register(r'dashboard-widgets', DashboardWidgetViewSet, basename='dashboard-widget')

urlpatterns = [
    path('', include(router.urls)),
]
