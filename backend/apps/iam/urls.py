from django.urls import path
from apps.iam import views

urlpatterns = [
    path('sso/providers/', views.SSOProvidersView.as_view()),
    path('pam/request/', views.PAMRequestView.as_view()),
    path('pam/<uuid:session_id>/approve/', views.PAMApproveView.as_view()),
    path('roles/mine/', views.RoleMiningView.as_view()),
    path('audit/verify/', views.AuditVerifyView.as_view()),
    path('audit/evidence/', views.AuditEvidenceView.as_view()),
    path('compliance/<str:framework>/run/', views.ComplianceRunView.as_view()),
]
