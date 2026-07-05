from rest_framework import viewsets
from .models import Account, JournalEntry, CostCenter, Budget
from .serializers import AccountSerializer, JournalEntrySerializer, CostCenterSerializer, BudgetSerializer
from apps.core.mixins import CompanyScopedMixin


class AccountViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    company_field = 'company'


class JournalEntryViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    company_field = 'company'


class CostCenterViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    company_field = 'company'


class BudgetViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    filterset_fields = ['fiscal_year', 'status', 'cost_center', 'account']
    company_field = 'company'
