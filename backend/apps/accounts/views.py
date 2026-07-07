"""Accounts API views: Chart of Accounts, Journal Entries, Cost Centers, Budgets."""
from rest_framework import viewsets, permissions, serializers as drf_serializers
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.core.mixins import CompanyScopedMixin
from .models import Account, JournalEntry, JournalEntryLine, CostCenter, Budget
from .serializers import (AccountSerializer, JournalEntrySerializer,
                           CostCenterSerializer, BudgetSerializer)


class AccountViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['account_type', 'is_group', 'is_active']
    search_fields = ['account_name', 'account_number']


class JournalEntryViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = JournalEntry.objects.prefetch_related('lines').all()
    serializer_class = JournalEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'posting_date']


class CostCenterViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer


class BudgetViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
