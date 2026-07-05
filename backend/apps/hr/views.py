from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Employee, Department, Team, LeaveRequest, Payroll
from .serializers import (
    EmployeeSerializer, DepartmentSerializer, TeamSerializer,
    LeaveRequestSerializer, PayrollSerializer,
)
from apps.core.mixins import CompanyScopedMixin


class EmployeeViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['first_name', 'last_name', 'employee_id', 'email', 'national_id']
    filterset_fields = ['department', 'status', 'company']
    company_field = 'company'


class DepartmentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']
    company_field = 'company'


class TeamViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']
    filterset_fields = ['lead']
    company_field = 'company'


class LeaveRequestViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['employee', 'status', 'leave_type', 'year']
    company_field = 'employee__company'


class PayrollViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['employee', 'status']
    company_field = 'employee__company'
