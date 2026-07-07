from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Account, JournalEntry, CostCenter, Budget
from .serializers import AccountSerializer, JournalEntrySerializer, CostCenterSerializer, BudgetSerializer
from apps.core.mixins import CompanyScopedMixin


class AccountViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['root_type', 'account_type', 'is_group', 'is_active']
    company_field = 'company'

    @action(detail=False, methods=['get'])
    def trial_balance(self, request):
        """Every postable (non-group) account's debit/credit balance side
        by side. A healthy ledger always has total_debit == total_credit."""
        qs = self.filter_queryset(self.get_queryset()).filter(is_group=False)
        rows = []
        total_debit = total_credit = 0
        for acc in qs:
            bal = acc.balance
            is_debit_side = (acc.root_type or acc.account_type) in Account.DEBIT_INCREASES
            if is_debit_side:
                debit_balance = bal if bal >= 0 else 0
                credit_balance = -bal if bal < 0 else 0
            else:
                credit_balance = bal if bal >= 0 else 0
                debit_balance = -bal if bal < 0 else 0
            total_debit += debit_balance
            total_credit += credit_balance
            rows.append({
                'account_id': acc.id, 'account_number': acc.account_number, 'account_name': acc.account_name,
                'root_type': acc.root_type or acc.account_type,
                'debit_balance': debit_balance, 'credit_balance': credit_balance,
            })
        return Response({
            'rows': rows, 'total_debit': total_debit, 'total_credit': total_credit,
            'balanced': total_debit == total_credit,
        })

    @action(detail=False, methods=['get'])
    def financial_statements(self, request):
        """A minimal Income Statement + Balance Sheet computed straight from
        live account balances — no separate reporting model to keep in sync."""
        qs = self.filter_queryset(self.get_queryset()).filter(is_group=False)

        def total_for(root_type):
            return qs.filter(root_type=root_type).aggregate(total=Sum('balance'))['total'] or 0

        total_income = total_for('Income')
        total_expense = total_for('Expense')
        net_income = total_income - total_expense

        total_assets = total_for('Asset')
        total_liabilities = total_for('Liability')
        total_equity = total_for('Equity') + net_income  # retained earnings roll into equity

        return Response({
            'income_statement': {
                'total_income': total_income, 'total_expense': total_expense, 'net_income': net_income,
            },
            'balance_sheet': {
                'total_assets': total_assets, 'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'balanced': total_assets == (total_liabilities + total_equity),
            },
        })


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
