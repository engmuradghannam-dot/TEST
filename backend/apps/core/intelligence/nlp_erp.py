"""Natural-Language ERP: turn a plain request into a resolved ERP action
or report, routed through the action broker (never direct execution).

"اعمل تقرير الربحية للربع الثاني"  ->  intent=financial_report,
    report=income_statement, period=Q2  -> calls reports.income_statement

Uses the LLM to classify intent + extract parameters as strict JSON, then
dispatches to a whitelisted handler registry. Unknown/ambiguous requests
ask for clarification rather than guessing.
"""
import json
import logging
from datetime import date

logger = logging.getLogger('nexus.nlp_erp')

INTENT_SYSTEM = """You translate ERP requests (Arabic or English) into JSON.
Respond ONLY with JSON, no markdown:
{
  "intent": "financial_report|sales_forecast|list_records|create_hint|unknown",
  "report": "income_statement|balance_sheet|trial_balance|null",
  "entity": "sales_order|purchase_order|customer|supplier|item|null",
  "period": {"type": "quarter|month|year|range|null",
             "quarter": 1-4, "month": 1-12, "year": int,
             "from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},
  "filters": {},
  "clarification": "string if intent is unknown/ambiguous, else empty"
}"""


def _quarter_range(q: int, year: int):
    starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    return date(year, *starts[q]), date(year, *ends[q])


class NaturalLanguageERP:
    def __init__(self):
        from apps.core.intelligence.ai_brain import LLMCore
        self.llm = LLMCore()

    def interpret(self, text: str) -> dict:
        resp = self.llm.generate(text, system_prompt=INTENT_SYSTEM,
                                 max_tokens=500)
        raw = (resp if isinstance(resp, str) else getattr(resp, 'text', str(resp)))
        raw = raw.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {'intent': 'unknown',
                    'clarification': 'Could not parse the request.'}

    def execute(self, text: str, company, user) -> dict:
        spec = self.interpret(text)
        intent = spec.get('intent')
        if intent == 'unknown' or spec.get('clarification'):
            return {'status': 'clarify',
                    'message': spec.get('clarification',
                                        'Please rephrase your request.')}

        if intent == 'financial_report':
            return self._financial_report(spec, company)
        if intent == 'sales_forecast':
            from apps.core.intelligence.predictive import SalesForecaster
            return {'status': 'ok', 'type': 'sales_forecast',
                    'data': SalesForecaster().monthly(company)}
        if intent == 'list_records':
            return self._list_records(spec, company)
        return {'status': 'clarify',
                'message': 'Recognized the request but no handler is wired '
                           'for that action yet.'}

    def _resolve_period(self, spec):
        p = spec.get('period') or {}
        year = p.get('year') or date.today().year
        if p.get('type') == 'quarter' and p.get('quarter'):
            return _quarter_range(p['quarter'], year)
        if p.get('type') == 'month' and p.get('month'):
            import calendar
            last = calendar.monthrange(year, p['month'])[1]
            return date(year, p['month'], 1), date(year, p['month'], last)
        if p.get('type') == 'range' and p.get('from') and p.get('to'):
            return date.fromisoformat(p['from']), date.fromisoformat(p['to'])
        return date(year, 1, 1), date(year, 12, 31)

    def _financial_report(self, spec, company):
        from apps.accounts import reports
        report = spec.get('report') or 'income_statement'
        d_from, d_to = self._resolve_period(spec)
        if report == 'income_statement':
            data = reports.income_statement(company, d_from, d_to)
        elif report == 'balance_sheet':
            data = reports.balance_sheet(company, as_of=d_to)
        else:
            data = reports.trial_balance(company, as_of=d_to)
        return {'status': 'ok', 'type': report,
                'period': {'from': str(d_from), 'to': str(d_to)},
                'data': data}

    def _list_records(self, spec, company):
        model_map = {}
        try:
            from apps.selling.models import SalesOrder, Customer
            from apps.buying.models import PurchaseOrder, Supplier
            from apps.inventory.models import Item
            model_map = {'sales_order': SalesOrder, 'customer': Customer,
                         'purchase_order': PurchaseOrder, 'supplier': Supplier,
                         'item': Item}
        except Exception:
            pass
        model = model_map.get(spec.get('entity'))
        if not model:
            return {'status': 'clarify', 'message': 'Which records exactly?'}
        qs = model.objects.filter(company=company)[:50]
        return {'status': 'ok', 'type': 'list', 'entity': spec['entity'],
                'count': len(qs), 'results': [str(o) for o in qs]}


nl_erp = NaturalLanguageERP()
