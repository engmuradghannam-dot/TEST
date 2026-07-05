from django.db.models import Q
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from apps.core.mixins import CompanyScopedMixin


class ProjectViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['project_name', 'project_code']
    filterset_fields = ['status', 'company']
    company_field = 'company'


class TaskViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """
    Company-scoped by project->company (via CompanyScopedMixin).
    On top of the tenant boundary, regular employees only see tasks that
    were actually assigned to them personally OR to a team they belong to
    -- managers/staff/superusers keep the full company-wide view.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['subject', 'project__project_name']
    filterset_fields = ['status', 'priority', 'project', 'team', 'assigned_to']
    company_field = 'project__company'

    def get_queryset(self):
        qs = super().get_queryset()  # already scoped to the user's company
        user = self.request.user

        if user.is_superuser or user.is_staff:
            return qs

        employee = getattr(user, 'employee_profile', None)
        if not employee:
            # A logged-in user with no linked Employee record has no
            # personal or team tasks to see.
            return qs.none()

        return qs.filter(
            Q(assigned_to=employee) | Q(team__members=employee)
        ).distinct()
