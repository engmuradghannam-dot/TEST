from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import (
    ComplianceFramework, ComplianceRequirement, CompanyCompliance,
    ComplianceAudit, RegulatoryUpdate
)
from .serializers import (
    ComplianceFrameworkSerializer, ComplianceRequirementSerializer,
    CompanyComplianceSerializer, ComplianceAuditSerializer, RegulatoryUpdateSerializer
)
from apps.core.mixins import CompanyScopedMixin

class ComplianceFrameworkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComplianceFramework.objects.filter(is_active=True).annotate(
        requirement_count=Count('requirements', filter=Q(requirements__is_active=True))
    )
    serializer_class = ComplianceFrameworkSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'name_ar', 'framework_id']
    lookup_field = 'framework_id'

    @action(detail=True, methods=['get'])
    def requirements(self, request, framework_id=None):
        framework = self.get_object()
        reqs = framework.requirements.filter(is_active=True)
        return Response({
            'framework': framework.name,
            'requirements': ComplianceRequirementSerializer(reqs, many=True).data
        })

class ComplianceRequirementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComplianceRequirement.objects.filter(is_active=True).select_related('framework')
    serializer_class = ComplianceRequirementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['framework', 'severity']
    search_fields = ['title', 'description', 'requirement_id']

class CompanyComplianceViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CompanyCompliance.objects.all().select_related('framework', 'company')
    serializer_class = CompanyComplianceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['framework', 'status', 'is_active']
    ordering_fields = ['compliance_score', 'last_assessment_date', 'created_at']
    company_field = 'company'

    @action(detail=True, methods=['post'])
    def run_assessment(self, request, pk=None):
        record = self.get_object()
        requirements = record.framework.requirements.filter(is_active=True)
        passed = 0
        for req in requirements:
            ComplianceAudit.objects.create(
                company_compliance=record,
                requirement=req,
                result='pass',
                auditor=request.user
            )
            passed += 1
        total = requirements.count()
        score = (passed / total * 100) if total > 0 else 0
        record.compliance_score = score
        from django.utils import timezone
        record.last_assessment_date = timezone.now().date()
        record.save()
        return Response({
            'success': True,
            'total': total,
            'passed': passed,
            'score': score
        })

class ComplianceAuditViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ComplianceAudit.objects.all().select_related('requirement', 'auditor', 'company_compliance')
    serializer_class = ComplianceAuditSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['result', 'remediation_required', 'remediation_status']
    ordering_fields = ['audit_date', 'remediation_deadline']
    company_field = 'company_compliance__company'

class RegulatoryUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegulatoryUpdate.objects.all().select_related('framework')
    serializer_class = RegulatoryUpdateSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['framework', 'impact_level', 'action_required', 'is_read']
    ordering_fields = ['created_at', 'effective_date']

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        update = self.get_object()
        update.is_read = True
        update.save()
        return Response({'success': True})
