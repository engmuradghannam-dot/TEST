from rest_framework import viewsets, permissions, filters
from apps.core.mixins import CompanyScopedMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from .models import Workflow, WorkflowState, WorkflowTransition, ApprovalStep, ApprovalRecord
from .serializers import WorkflowSerializer, WorkflowStateSerializer, WorkflowTransitionSerializer, ApprovalStepSerializer, ApprovalRecordSerializer
from apps.core.mixins import AuditUserMixin


class WorkflowViewSet(AuditUserMixin, viewsets.ModelViewSet):
    """Workflow definitions are cross-tenant system configuration
    (they have no `company` field), so they are restricted to staff/admin
    users instead of being company-scoped like business data."""
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'document_type']
    permission_classes = [permissions.IsAdminUser]


class ApprovalStepViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ApprovalStep.objects.all()
    serializer_class = ApprovalStepSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workflow', 'approver', 'is_required']
    company_field = 'workflow__company'


class ApprovalRecordViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ApprovalRecord.objects.all()
    serializer_class = ApprovalRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'document_type', 'requested_by', 'approver']
    company_field = 'step__workflow__company'

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        record.status = 'Approved'
        record.approver = request.user
        record.responded_at = timezone.now()
        record.comments = request.data.get('comments', '')
        record.save()
        return Response(ApprovalRecordSerializer(record).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        record = self.get_object()
        record.status = 'Rejected'
        record.approver = request.user
        record.responded_at = timezone.now()
        record.comments = request.data.get('comments', '')
        record.save()
        return Response(ApprovalRecordSerializer(record).data)
