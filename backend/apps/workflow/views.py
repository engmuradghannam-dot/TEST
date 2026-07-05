from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter
from .models import Workflow, WorkflowState, WorkflowTransition
from .serializers import WorkflowSerializer, WorkflowStateSerializer, WorkflowTransitionSerializer


class WorkflowViewSet(viewsets.ModelViewSet):
    """Workflow definitions are cross-tenant system configuration
    (they have no `company` field), so they are restricted to staff/admin
    users instead of being company-scoped like business data."""
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'document_type']
    permission_classes = [permissions.IsAdminUser]
