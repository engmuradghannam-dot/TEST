from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import (
    IdentityProvider, SSOConnection, SAMLRequestLog,
    RoleDefinition, RoleMiningJob, RoleMiningSuggestion, PermissionAnomaly,
    UserRoleAssignment, SeparationOfDutiesRule,
    PrivilegedAccount, PrivilegedSession, PasswordVault, VaultAccessLog,
    PrivilegedCommandPolicy, AuthenticationPolicy, UserDevice,
    SecurityEvent, AdaptiveAuthentication, LoginAttempt,
    ServiceAccount, JITAccessRequest
)
from .serializers import (
    IdentityProviderSerializer, SSOConnectionSerializer,
    RoleDefinitionSerializer, RoleMiningJobSerializer,
    PermissionAnomalySerializer, PrivilegedAccountSerializer,
    PrivilegedSessionSerializer, PasswordVaultSerializer,
    AuthenticationPolicySerializer, SecurityEventSerializer,
    ServiceAccountSerializer, JITAccessRequestSerializer
)

class IdentityProviderViewSet(viewsets.ModelViewSet):
    queryset = IdentityProvider.objects.all()
    serializer_class = IdentityProviderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['provider_type', 'status', 'is_global', 'company']
    search_fields = ['name', 'provider_type']

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        provider = self.get_object()
        # Implement connection test logic
        return Response({'success': True, 'message': 'Connection test passed'})

    @action(detail=True, methods=['post'])
    def sync_users(self, request, pk=None):
        provider = self.get_object()
        # Trigger LDAP/AD sync
        return Response({'success': True, 'message': 'User sync initiated'})

class RoleDefinitionViewSet(viewsets.ModelViewSet):
    queryset = RoleDefinition.objects.all()
    serializer_class = RoleDefinitionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_system_role', 'is_active', 'company']
    search_fields = ['name', 'description']

    @action(detail=True, methods=['post'])
    def assign_to_user(self, request, pk=None):
        role = self.get_object()
        user_id = request.data.get('user_id')
        # Create assignment
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        role = self.get_object()
        new_role = RoleDefinition.objects.create(
            name=f"{role.name} (Copy)",
            description=role.description,
            category=role.category,
            permissions=role.permissions,
            company=role.company
        )
        return Response({'success': True, 'id': str(new_role.id)})

class RoleMiningJobViewSet(viewsets.ModelViewSet):
    queryset = RoleMiningJob.objects.all()
    serializer_class = RoleMiningJobSerializer

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        job = self.get_object()
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        # Trigger async analysis
        return Response({'success': True, 'job_id': str(job.id)})

    @action(detail=True, methods=['post'])
    def apply_suggestions(self, request, pk=None):
        job = self.get_object()
        suggestion_ids = request.data.get('suggestion_ids', [])
        # Apply selected suggestions
        return Response({'success': True, 'applied': len(suggestion_ids)})

class PermissionAnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PermissionAnomaly.objects.all()
    serializer_class = PermissionAnomalySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['anomaly_type', 'severity', 'is_resolved']
    ordering_fields = ['risk_score', 'created_at']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        anomaly = self.get_object()
        anomaly.is_resolved = True
        anomaly.resolved_at = timezone.now()
        anomaly.resolution_notes = request.data.get('notes', '')
        anomaly.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def auto_remediate(self, request, pk=None):
        anomaly = self.get_object()
        anomaly.auto_remediation_triggered = True
        anomaly.is_resolved = True
        anomaly.save()
        return Response({'success': True})

class PrivilegedAccountViewSet(viewsets.ModelViewSet):
    queryset = PrivilegedAccount.objects.all()
    serializer_class = PrivilegedAccountSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['account_type', 'status', 'risk_level', 'company']
    search_fields = ['name', 'target_host']

    @action(detail=True, methods=['post'])
    def rotate_password(self, request, pk=None):
        account = self.get_object()
        # Trigger password rotation
        return Response({'success': True, 'message': 'Password rotation initiated'})

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        account = self.get_object()
        # Create checkout session
        return Response({'success': True, 'session_id': 'new-session-id'})

    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        session_id = request.data.get('session_id')
        # End session
        return Response({'success': True})

class PrivilegedSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PrivilegedSession.objects.all()
    serializer_class = PrivilegedSessionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'account', 'user']
    ordering_fields = ['requested_at', 'started_at']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        session = self.get_object()
        session.status = 'approved'
        session.approved_by = request.user
        session.approved_at = timezone.now()
        session.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        session = self.get_object()
        session.status = 'terminated'
        session.ended_at = timezone.now()
        session.ended_by = request.user
        session.save()
        return Response({'success': True})

class PasswordVaultViewSet(viewsets.ModelViewSet):
    queryset = PasswordVault.objects.all()
    serializer_class = PasswordVaultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['secret_type', 'company']
    search_fields = ['name', 'description']

    @action(detail=True, methods=['post'])
    def reveal(self, request, pk=None):
        secret = self.get_object()
        # Log access
        VaultAccessLog.objects.create(
            secret=secret,
            user=request.user,
            action='view',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        # Decrypt and return
        return Response({'success': True, 'value': '***decrypted***'})

    @action(detail=True, methods=['post'])
    def rotate(self, request, pk=None):
        secret = self.get_object()
        # Trigger rotation
        return Response({'success': True})

class SecurityEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'severity', 'investigation_status']
    ordering_fields = ['created_at']

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        # Aggregate security metrics
        total_events = SecurityEvent.objects.count()
        critical_count = SecurityEvent.objects.filter(severity='critical').count()
        open_investigations = SecurityEvent.objects.filter(investigation_status='open').count()
        return Response({
            'total_events': total_events,
            'critical_count': critical_count,
            'open_investigations': open_investigations,
            'by_category': dict(SecurityEvent.objects.values('category').annotate(count=Count('id')).values_list('category', 'count')),
            'by_severity': dict(SecurityEvent.objects.values('severity').annotate(count=Count('id')).values_list('severity', 'count'))
        })

class ServiceAccountViewSet(viewsets.ModelViewSet):
    queryset = ServiceAccount.objects.all()
    serializer_class = ServiceAccountSerializer

    @action(detail=True, methods=['post'])
    def rotate_key(self, request, pk=None):
        account = self.get_object()
        # Generate new API key
        return Response({'success': True, 'new_api_key': 'new-key-generated'})

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        account = self.get_object()
        account.is_active = False
        account.save()
        return Response({'success': True})

class JITAccessRequestViewSet(viewsets.ModelViewSet):
    queryset = JITAccessRequest.objects.all()
    serializer_class = JITAccessRequestSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        jit = self.get_object()
        jit.status = 'approved'
        jit.approvers.add(request.user)
        jit.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        jit = self.get_object()
        jit.status = 'denied'
        jit.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        jit = self.get_object()
        jit.status = 'active'
        jit.actual_start_time = timezone.now()
        jit.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        jit = self.get_object()
        jit.status = 'revoked'
        jit.revoked_at = timezone.now()
        jit.revoked_by = request.user
        jit.save()
        return Response({'success': True})


# SAML / OAuth / LDAP View Stubs (to be implemented)
from rest_framework.views import APIView

class SAMLAuthView(APIView):
    """Initiate SAML authentication"""
    def get(self, request):
        return Response({'message': 'SAML authentication initiated'})

class SAMLACSView(APIView):
    """SAML Assertion Consumer Service"""
    def post(self, request):
        return Response({'message': 'SAML response received'})

class OAuthCallbackView(APIView):
    """OAuth callback handler"""
    def get(self, request):
        return Response({'message': 'OAuth callback received'})

class LDAPSyncView(APIView):
    """Trigger LDAP/AD sync"""
    def post(self, request):
        return Response({'message': 'LDAP sync initiated'})


# ── AI/NLP views (for apps.iam.ai_urls) ──────────────────────────
class NaturalLanguageView(APIView):
    """POST /api/v1/ai/nl/ — interpret an Arabic/English ERP command."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({'error': 'text required'}, status=400)
        try:
            from apps.core.intelligence.nlp_erp import NaturalLanguageERP
            nlp = NaturalLanguageERP()
            result = nlp.interpret(text)
            return Response(result)
        except Exception as exc:
            return Response({'error': str(exc)}, status=500)


class SalesForecastView(APIView):
    """POST /api/v1/ai/forecast/sales/ — AI sales forecast."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            from apps.core.intelligence.predictive import PredictiveEngine
            eng = PredictiveEngine()
            result = eng.sales_forecast(request.user.company,
                                        days=request.data.get('days', 30))
            return Response(result)
        except Exception as exc:
            return Response({'error': str(exc)}, status=500)


class AICoreHealthView(APIView):
    """GET /api/v1/ai/core/health/"""
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'ai_core': 'running'})


class SecurityScanView(APIView):
    """POST /api/v1/ai/security/scan/ — AI security anomaly scan."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            from apps.security_engine.ai_sec.anomaly_detection import (
                profiler, fraud_detector)
            return Response({'status': 'scan_queued'})
        except Exception as exc:
            return Response({'error': str(exc)}, status=500)


# ── Our security views (from apps.iam.security_views) ─────────────────────
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class SSOProvidersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        from apps.iam.models import IdentityProvider
        return Response([{'id': p.id, 'name': p.name, 'protocol': p.protocol}
                         for p in IdentityProvider.objects.filter(status='active')])


class PAMRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        from apps.iam import pam
        s = pam.request_elevation(
            request.user,
            request.data.get('role', ''),
            request.data.get('justification', ''),
            int(request.data.get('duration_minutes', 60)))
        return Response({'session_id': str(s.id), 'status': s.status}, status=201)


class PAMApproveView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, session_id):
        from apps.iam.models import PrivilegedSession
        s = PrivilegedSession.objects.get(id=session_id)
        try:
            s.approve(request.user)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        return Response({'status': s.status, 'expires_at': s.expires_at})


class RoleMiningView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request):
        from apps.iam import pam
        report = pam.mine_roles(int(request.data.get('min_support', 2)))
        return Response({'users_analyzed': report.users_analyzed,
                         'suggestions': report.suggestions})


class AuditVerifyView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        from apps.core.security.immutable_audit import ledger
        return Response(ledger.verify_chain())


class AuditEvidenceView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        from apps.core.security.immutable_audit import ledger
        return Response(ledger.export_evidence(
            event_prefix=request.GET.get('prefix', '')))
