from django.db.models import Q, Sum
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Project, Task, Milestone, Stakeholder, RiskRegister, IssueLog, ChangeRequest, TimeEntry, TaskComment
from .serializers import (
    ProjectSerializer, TaskSerializer, MilestoneSerializer, StakeholderSerializer,
    RiskRegisterSerializer, IssueLogSerializer, ChangeRequestSerializer,
    TimeEntrySerializer, TaskCommentSerializer,
)
from apps.core.mixins import CompanyScopedMixin


class ProjectViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['project_name', 'project_code']
    filterset_fields = ['status', 'company', 'priority', 'owner']
    company_field = 'company'

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Gantt chart data: tasks + milestones with dates."""
        project = self.get_object()
        tasks_data = []
        for task in project.tasks.all():
            tasks_data.append({
                'id': f"task_{task.id}",
                'type': 'task',
                'name': task.subject,
                'status': task.status,
                'start': task.expected_start.isoformat() if task.expected_start else None,
                'end': task.expected_end.isoformat() if task.expected_end else None,
                'progress': 100 if task.status == 'Completed' else (50 if task.status == 'Working' else 0),
                'assignee': task.assigned_to.first_name if task.assigned_to else None,
            })
        for milestone in project.milestones.all():
            tasks_data.append({
                'id': f"milestone_{milestone.id}",
                'type': 'milestone',
                'name': milestone.name,
                'status': milestone.status,
                'start': milestone.due_date.isoformat(),
                'end': milestone.due_date.isoformat(),
                'progress': 100 if milestone.status == 'Achieved' else 0,
            })
        return Response({'project_name': project.project_name, 'items': tasks_data})

    @action(detail=True, methods=['get'])
    def kanban(self, request, pk=None):
        """Kanban board data: tasks grouped by status."""
        project = self.get_object()
        columns = {}
        for status_choice, _ in Task.STATUS_CHOICES:
            columns[status_choice] = []
        for task in project.tasks.all():
            columns[task.status].append({
                'id': task.id,
                'subject': task.subject,
                'priority': task.priority,
                'assignee': task.assigned_to.first_name if task.assigned_to else None,
                'expected_end': task.expected_end.isoformat() if task.expected_end else None,
                'comments_count': task.comments.count(),
                'total_hours': sum((te.duration_hours for te in task.time_entries.all()), 0),
            })
        return Response(columns)

    @action(detail=True, methods=['get'])
    def time_report(self, request, pk=None):
        """Time tracking report for the project."""
        project = self.get_object()
        entries = project.time_entries.all()
        by_employee = {}
        for entry in entries:
            emp_name = entry.employee.first_name or str(entry.employee)
            if emp_name not in by_employee:
                by_employee[emp_name] = {'hours': 0, 'cost': 0, 'entries': 0}
            by_employee[emp_name]['hours'] += entry.duration_hours
            by_employee[emp_name]['cost'] += float(entry.cost)
            by_employee[emp_name]['entries'] += 1
        return Response({
            'total_hours': sum(e['hours'] for e in by_employee.values()),
            'total_cost': sum(e['cost'] for e in by_employee.values()),
            'by_employee': by_employee,
        })


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
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return qs
        employee = getattr(user, 'employee_profile', None)
        if not employee:
            return qs.none()
        return qs.filter(
            Q(assigned_to=employee) | Q(team__members=employee)
        ).distinct()

    @action(detail=True, methods=['post'])
    def start_timer(self, request, pk=None):
        """Start a new time entry for this task."""
        task = self.get_object()
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response({'error': 'No employee profile linked to user.'}, status=status.HTTP_400_BAD_REQUEST)
        entry = TimeEntry.objects.create(
            task=task, project=task.project, employee=employee,
            start_time=request.data.get('start_time'),
            hourly_rate=employee.salary / 160 if employee.salary else 0,  # rough hourly rate
        )
        return Response(TimeEntrySerializer(entry).data)

    @action(detail=True, methods=['post'])
    def stop_timer(self, request, pk=None):
        """Stop the active time entry for this task."""
        task = self.get_object()
        employee = getattr(request.user, 'employee_profile', None)
        entry = task.time_entries.filter(employee=employee, end_time__isnull=True).first()
        if not entry:
            return Response({'error': 'No active timer found.'}, status=status.HTTP_400_BAD_REQUEST)
        entry.end_time = request.data.get('end_time')
        entry.save()
        return Response(TimeEntrySerializer(entry).data)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for this task."""
        task = self.get_object()
        comments = task.comments.filter(parent__isnull=True)
        serializer = TaskCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)


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


class TimeEntryViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task', 'project', 'employee', 'entry_type', 'is_billable']
    company_field = 'project__company'

    @action(detail=False, methods=['get'])
    def my_entries(self, request):
        """Get current user's time entries."""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response([])
        entries = self.get_queryset().filter(employee=employee)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Time tracking dashboard summary."""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response({'error': 'No employee profile.'}, status=status.HTTP_400_BAD_REQUEST)
        entries = self.get_queryset().filter(employee=employee)
        today = entries.filter(start_time__date__gte='2024-01-01')  # simplified
        return Response({
            'total_hours_this_month': sum((e.duration_hours for e in entries), 0),
            'total_entries': entries.count(),
            'billable_hours': sum((e.duration_hours for e in entries.filter(is_billable=True)), 0),
            'non_billable_hours': sum((e.duration_hours for e in entries.filter(is_billable=False)), 0),
        })


class TaskCommentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = TaskComment.objects.all()
    serializer_class = TaskCommentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task', 'author']
    company_field = 'task__project__company'

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
