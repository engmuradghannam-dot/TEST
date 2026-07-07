from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ComplianceFrameworkViewSet, ComplianceRequirementViewSet,
    CompanyComplianceViewSet, ComplianceAuditViewSet, RegulatoryUpdateViewSet
)

router = DefaultRouter()
router.register(r'frameworks', ComplianceFrameworkViewSet, basename='compliance-framework')
router.register(r'requirements', ComplianceRequirementViewSet, basename='compliance-requirement')
router.register(r'company-records', CompanyComplianceViewSet, basename='company-compliance')
router.register(r'audits', ComplianceAuditViewSet, basename='compliance-audit')
router.register(r'regulatory-updates', RegulatoryUpdateViewSet, basename='regulatory-update')

urlpatterns = [
    path('', include(router.urls)),
]
