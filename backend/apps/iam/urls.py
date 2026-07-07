"""IAM module: Identity providers, PAM, audit trail."""
from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.iam.views import (
    IdentityProviderViewSet, PrivilegedSessionViewSet,
    RoleMiningJobViewSet, SecurityEventViewSet,
    SSOProvidersView, PAMRequestView, PAMApproveView,
    RoleMiningView, AuditVerifyView, AuditEvidenceView,
)

router = DefaultRouter()
router.register(r'providers', IdentityProviderViewSet)
router.register(r'privileged-sessions', PrivilegedSessionViewSet)
router.register(r'role-mining-jobs', RoleMiningJobViewSet)
router.register(r'security-events', SecurityEventViewSet)

urlpatterns = router.urls + [
    path('sso/providers/', SSOProvidersView.as_view()),
    path('pam/request/', PAMRequestView.as_view()),
    path('pam/<uuid:session_id>/approve/', PAMApproveView.as_view()),
    path('roles/mine/', RoleMiningView.as_view()),
    path('audit/verify/', AuditVerifyView.as_view()),
    path('audit/evidence/', AuditEvidenceView.as_view()),
]
