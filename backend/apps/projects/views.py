from django.db.models import Q
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Project, Task, Milestone, Stakeholder, RiskRegister, IssueLog, ChangeRequest
from .serializers import (
    ProjectSerializer, TaskSerializer, MilestoneSerializer, StakeholderSerializer,
    RiskRegisterSerializer, IssueLogSerializer, ChangeRequestSerializer,
)
from apps.core.mixins import CompanyScopedMixin


class ProjectViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['project_name', 'project_code']
    filterset_fields = ['status', 'company', 'priority', 'owner']
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
            return qs.none()

        return qs.filter(
            Q(assigned_to=employee) | Q(team__members=employee)
        ).distinct()


class MilestoneViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status']
    company_field = 'project__company'


class StakeholderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'organization']
    filterset_fields = ['project', 'influence', 'interest']
    company_field = 'project__company'


class RiskRegisterViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = RiskRegister.objects.all()
    serializer_class = RiskRegisterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title']
    filterset_fields = ['project', 'status', 'category']
    company_field = 'project__company'


class IssueLogViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = IssueLog.objects.all()
    serializer_class = IssueLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title']
    filterset_fields = ['project', 'status', 'severity']
    company_field = 'project__company'


class ChangeRequestViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ChangeRequest.objects.all()
    serializer_class = ChangeRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['title']
    filterset_fields = ['project', 'status']
    company_field = 'project__company'
