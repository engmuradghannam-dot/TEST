from rest_framework import viewsets, status, filters
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Company, Branch, Warehouse, PrintTemplate, Module, AuditLog
from .serializers import (
    UserSerializer, CompanySerializer, BranchSerializer, WarehouseSerializer,
    PrintTemplateSerializer, ModuleSerializer, AuditLogSerializer
)
from .mixins import CompanyScopedMixin, AuditUserMixin


class UserViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    company_field = 'company'


class CompanyViewSet(AuditUserMixin, viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'tax_id']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.none()
        if user.is_superuser:
            return qs
        if not user.company_id:
            return qs.none()
        return qs.filter(id=user.company_id)


class BranchViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'address', 'branch_code']
    company_field = 'company'


class WarehouseViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'code']
    company_field = 'branch__company'


class PrintTemplateViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = PrintTemplate.objects.all()
    serializer_class = PrintTemplateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']
    filterset_fields = ['document_type', 'is_active', 'is_default']
    company_field = 'company'


class ModuleViewSet(AuditUserMixin, viewsets.ModelViewSet):
    """System-wide module list (Accounts, HR, Inventory, ...). Not tenant-scoped
    since modules are the same catalog for every company; restricted to staff
    to prevent regular users from editing the module catalog itself."""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'code']

    def get_permissions(self):
        from rest_framework import permissions
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only, staff-only. Audit entries are written exclusively by
    signal handlers (apps.core.audit) — there is no create/update/delete
    action here on purpose."""
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'app_label', 'model_name', 'object_id', 'user']

    def get_permissions(self):
        from rest_framework import permissions
        return [permissions.IsAdminUser()]


class UIScreenViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """Low-code screen definitions consumed by the frontend FormEngine."""
    from apps.core.models import UIScreen
    from apps.core.serializers import UIScreenSerializer
    queryset = UIScreen.objects.all()
    serializer_class = UIScreenSerializer
    lookup_field = 'slug'

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company,
                        created_by=self.request.user)
