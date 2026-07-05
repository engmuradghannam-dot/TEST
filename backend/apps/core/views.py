from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import User, Company, Branch, Warehouse, PrintTemplate
from .serializers import UserSerializer, CompanySerializer, BranchSerializer, WarehouseSerializer, PrintTemplateSerializer
from .mixins import CompanyScopedMixin


class UserViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    company_field = 'company'


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'tax_id']

    def get_queryset(self):
        # Company IS the tenant boundary, so it's scoped by id, not by a
        # 'company' field on itself.
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
    search_fields = ['name', 'address']
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
