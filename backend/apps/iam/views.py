"""IAM + AI-core + security API endpoints, mounted under /api/v1/iam/
and /api/v1/ai/."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser


def _company(request):
    return getattr(request.user, 'company', None)


class SSOProvidersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import IdentityProvider
        return Response([{'id': p.id, 'name': p.name, 'protocol': p.protocol}
                         for p in IdentityProvider.objects.filter(is_active=True)])


class PAMRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.iam import pam
        s = pam.request_elevation(
            request.user, request.data.get('role', ''),
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


class NaturalLanguageView(APIView):
    """POST {"text": "اعمل تقرير الربحية للربع الثاني"} -> resolved action."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.core.intelligence.nlp_erp import nl_erp
        return Response(nl_erp.execute(
            request.data.get('text', ''), _company(request), request.user))


class SalesForecastView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.core.intelligence.predictive import SalesForecaster
        return Response(SalesForecaster().monthly(_company(request)))


class AICoreHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.core.intelligence.ai_core import ai_core
        return Response(ai_core.health())


class SecurityScanView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        from apps.core.security.ai_security import orchestrator
        return Response({'findings': orchestrator.run_scan()})


class ComplianceRunView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, framework):
        from apps.compliance.automation import engine
        return Response(engine.run_framework(framework, _company(request)))
