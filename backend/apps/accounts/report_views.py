"""Financial report API endpoints (part of the Reporting/BI layer).

GET /api/v1/accounts/reports/trial-balance/?as_of=2026-12-31
GET /api/v1/accounts/reports/income-statement/?from=2026-01-01&to=2026-12-31
GET /api/v1/accounts/reports/balance-sheet/?as_of=2026-12-31
GET /api/v1/accounts/reports/kpis/
Add &format=xlsx to any statement for an Excel download.
"""
import io
from datetime import date

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.accounts import reports


def _company(request):
    return getattr(request.user, 'company', None) or request.user.company


def _parse(qs, key):
    v = qs.get(key)
    return date.fromisoformat(v) if v else None


def _xlsx(data: dict, sheet: str) -> HttpResponse:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = sheet[:31]
    rows = (data.get('rows') or data.get('income', []) + data.get('expenses', [])
            or data.get('assets', []) + data.get('liabilities', [])
            + data.get('equity', []))
    if rows:
        headers = list(rows[0].keys())
        ws.append([h.title() for h in headers])
        for r in rows:
            ws.append([str(r[h]) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    resp = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument'
                     '.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{sheet}.xlsx"'
    return resp


class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = reports.trial_balance(_company(request),
                                     as_of=_parse(request.GET, 'as_of'))
        if request.GET.get('format') == 'xlsx':
            return _xlsx(data, 'trial_balance')
        return Response(data)


class IncomeStatementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        data = reports.income_statement(
            _company(request),
            date_from=_parse(request.GET, 'from') or today.replace(month=1, day=1),
            date_to=_parse(request.GET, 'to') or today)
        if request.GET.get('format') == 'xlsx':
            return _xlsx(data, 'income_statement')
        return Response(data)


class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = reports.balance_sheet(_company(request),
                                     as_of=_parse(request.GET, 'as_of'))
        if request.GET.get('format') == 'xlsx':
            return _xlsx(data, 'balance_sheet')
        return Response(data)


class FinancialKPIsView(APIView):
    """Real-time headline KPIs for dashboards."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = _company(request)
        today = date.today()
        pl = reports.income_statement(
            company, today.replace(month=1, day=1), today)
        bs = reports.balance_sheet(company, as_of=today)
        return Response({
            'net_profit_ytd': pl['net_profit'],
            'total_income_ytd': pl['total_income'],
            'total_expense_ytd': pl['total_expense'],
            'total_assets': bs['total_assets'],
            'books_balanced': bs['is_balanced'],
            'as_of': str(today),
        })
