from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IndustryCatalogViewSet, IndustryControlViewSet,
    AIAgentRegistryViewSet, CompanyIndustryProfileViewSet,
    ControlExecutionLogViewSet
)

router = DefaultRouter()
router.register(r'catalog', IndustryCatalogViewSet, basename='industry-catalog')
router.register(r'controls', IndustryControlViewSet, basename='industry-control')
router.register(r'ai-agents', AIAgentRegistryViewSet, basename='ai-agent')
router.register(r'company-profiles', CompanyIndustryProfileViewSet, basename='company-industry-profile')
router.register(r'execution-logs', ControlExecutionLogViewSet, basename='control-execution-log')

urlpatterns = [
    path('', include(router.urls)),
]
