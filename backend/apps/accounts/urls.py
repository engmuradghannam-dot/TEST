"""Auto-generated module router for apps.accounts."""
from rest_framework.routers import DefaultRouter
from apps.accounts.views import AccountViewSet, JournalEntryViewSet, CostCenterViewSet, BudgetViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'cost-centers', CostCenterViewSet)
router.register(r'budgets', BudgetViewSet)

from django.urls import path
from apps.accounts.report_views import (
    TrialBalanceView, IncomeStatementView, BalanceSheetView, FinancialKPIsView,
)

urlpatterns = router.urls + [
    path('reports/trial-balance/', TrialBalanceView.as_view()),
    path('reports/income-statement/', IncomeStatementView.as_view()),
    path('reports/balance-sheet/', BalanceSheetView.as_view()),
    path('reports/kpis/', FinancialKPIsView.as_view()),
]
