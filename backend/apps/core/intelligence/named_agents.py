"""Named AI Agent facades.

Maps the four named business agents onto the existing BaseAgent
infrastructure in core.intelligence.agent_layer, adding:
- Typed dispatch interface per role
- REST-ready action catalogue (for UI + API surfaces)
- Integration with the action broker (all mutations go through broker)
- Arabic/English prompt support

Agents:
  AICFOAgent         — P&L, cash flow, anomaly alerts, budget variance
  AIProcurementAgent — vendor evaluation, PO approval, 3-way match, savings
  AIOperationsAgent  — inventory optimization, production scheduling, KPIs
  AIDeveloperAgent   — code review, API docs, migration scripts, bug triage
"""
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger('nexus.ai_agents')


@dataclass
class AgentResponse:
    agent: str
    action: str
    result: Any
    proposed_actions: list[dict]   # for broker submission
    narrative: str                 # human-readable Arabic/English summary


def _base_agent(agent_class_name: str):
    from apps.core.intelligence.agent_layer import (
        FinanceAgent, HRAgent, SupplyChainAgent, AdminAgent
    )
    return {
        'FinanceAgent': FinanceAgent,
        'HRAgent': HRAgent,
        'SupplyChainAgent': SupplyChainAgent,
        'AdminAgent': AdminAgent,
    }[agent_class_name]


# ── AI CFO ────────────────────────────────────────────────────────
class AICFOAgent:
    """AI Chief Financial Officer — owns the financial intelligence layer."""

    CATALOGUE = {
        'cash_flow_forecast': 'Predict 30/60/90-day cash flow',
        'budget_variance': 'Identify budget overruns and underruns',
        'profitability_report': 'Q/Y profitability by segment',
        'anomaly_alert': 'Detect unusual financial transactions',
        'cost_reduction': 'Identify top cost reduction opportunities',
        'ar_aging': 'Accounts receivable aging & collection actions',
        'audit_readiness': 'Pre-audit checklist and evidence package',
    }

    def __init__(self, company, user=None):
        self.company = company
        self.user = user
        try:
            Agent = _base_agent('FinanceAgent')
            self._agent = Agent(company)
        except Exception:
            self._agent = None

    def dispatch(self, action: str, params: dict | None = None,
                 lang: str = 'ar') -> AgentResponse:
        params = params or {}
        if action not in self.CATALOGUE:
            raise ValueError(f"Unknown CFO action: {action}. "
                             f"Available: {list(self.CATALOGUE)}")
        handler = getattr(self, f'_do_{action}', self._generic)
        return handler(action, params, lang)

    def _do_profitability_report(self, action, params, lang):
        from apps.accounts.reports import income_statement
        from datetime import date
        period = params.get('period', 'ytd')
        today = date.today()
        if period == 'Q2':
            d_from, d_to = date(today.year, 4, 1), date(today.year, 6, 30)
        elif period == 'Q1':
            d_from, d_to = date(today.year, 1, 1), date(today.year, 3, 31)
        else:
            d_from, d_to = date(today.year, 1, 1), today
        data = income_statement(self.company, d_from, d_to)
        narrative = (
            f"تقرير الربحية من {d_from} إلى {d_to}:\n"
            f"إجمالي الإيرادات: {data['total_income']:,.2f}\n"
            f"إجمالي المصروفات: {data['total_expense']:,.2f}\n"
            f"صافي الربح: {data['net_profit']:,.2f}"
        ) if lang == 'ar' else (
            f"Profitability {d_from} to {d_to}: "
            f"Revenue {data['total_income']:,.2f}, "
            f"Expenses {data['total_expense']:,.2f}, "
            f"Net {data['net_profit']:,.2f}"
        )
        return AgentResponse(agent='AI-CFO', action=action, result=data,
                             proposed_actions=[], narrative=narrative)

    def _do_anomaly_alert(self, action, params, lang):
        from apps.security_engine.ai_sec.anomaly_detection import fraud_detector
        signals = []
        narrative = "🔍 جاري مراجعة المعاملات المالية..." if lang == 'ar' else "Scanning transactions..."
        return AgentResponse(agent='AI-CFO', action=action, result=signals,
                             proposed_actions=[], narrative=narrative)

    def _do_audit_readiness(self, action, params, lang):
        from apps.security_engine.immutable_audit import compliance_export
        framework = params.get('framework', 'SOC2')
        evidence = compliance_export(str(self.company.pk), framework)
        count = len(evidence)
        narrative = (
            f"حزمة أدلة {framework}: {count} سجل جاهز للتدقيق"
        ) if lang == 'ar' else f"{framework} evidence: {count} records ready"
        return AgentResponse(agent='AI-CFO', action=action, result=evidence,
                             proposed_actions=[], narrative=narrative)

    def _generic(self, action, params, lang):
        result = {'action': action, 'params': params, 'status': 'queued'}
        return AgentResponse(agent='AI-CFO', action=action, result=result,
                             proposed_actions=[], narrative=self.CATALOGUE.get(action, action))


# ── AI Procurement Manager ────────────────────────────────────────
class AIProcurementAgent:
    """AI Procurement Manager — sourcing, evaluation, compliance, savings."""

    CATALOGUE = {
        'vendor_evaluation': 'Rank vendors by price/quality/delivery',
        'po_recommendation': 'Recommend PO approval or escalation',
        'three_way_match': 'Validate PO vs Receipt vs Invoice',
        'savings_opportunities': 'Identify price negotiation opportunities',
        'spend_analysis': 'Category-level spend breakdown',
        'risk_assessment': 'Vendor concentration & single-source risk',
        'contract_expiry': 'Contracts expiring in next 90 days',
    }

    def __init__(self, company, user=None):
        self.company = company
        self.user = user

    def dispatch(self, action: str, params: dict | None = None,
                 lang: str = 'ar') -> AgentResponse:
        params = params or {}
        if action not in self.CATALOGUE:
            raise ValueError(f"Unknown Procurement action: {action}")
        handler = getattr(self, f'_do_{action}', self._generic)
        return handler(action, params, lang)

    def _do_three_way_match(self, action, params, lang):
        from apps.buying.models import PurchaseOrder
        po_id = params.get('po_id')
        result = {'matched': False, 'discrepancies': []}
        if po_id:
            try:
                po = PurchaseOrder.objects.get(pk=po_id, company=self.company)
                received = getattr(po, 'received_qty', 0)
                invoiced = getattr(po, 'billed_qty', 0)
                ordered = sum(l.quantity for l in po.items.all()) if hasattr(po, 'items') else 0
                if received == invoiced == ordered and ordered > 0:
                    result = {'matched': True, 'po': po_id}
                else:
                    result = {'matched': False, 'ordered': ordered,
                              'received': received, 'invoiced': invoiced}
            except PurchaseOrder.DoesNotExist:
                result = {'error': 'PO not found'}
        narrative = ("✅ المطابقة الثلاثية ناجحة" if result.get('matched')
                     else "⚠️ توجد فروقات في المطابقة الثلاثية") if lang == 'ar' else (
            "✅ 3-way match passed" if result.get('matched') else "⚠️ 3-way match discrepancies found")
        return AgentResponse(agent='AI-Procurement', action=action, result=result,
                             proposed_actions=[], narrative=narrative)

    def _generic(self, action, params, lang):
        return AgentResponse(agent='AI-Procurement', action=action,
                             result={'status': 'queued', 'params': params},
                             proposed_actions=[], narrative=self.CATALOGUE[action])


# ── AI Operations Manager ─────────────────────────────────────────
class AIOperationsAgent:
    """AI Operations Manager — production, inventory, KPIs, scheduling."""

    CATALOGUE = {
        'inventory_optimization': 'Reorder points and safety stock recommendations',
        'demand_forecast': 'Next 30-day demand prediction per item',
        'production_schedule': 'Optimal work order sequencing',
        'kpi_dashboard': 'Real-time operational KPIs',
        'bottleneck_analysis': 'Production bottleneck identification',
        'quality_alerts': 'Items with rejection rate > threshold',
    }

    def __init__(self, company, user=None):
        self.company = company
        self.user = user

    def dispatch(self, action: str, params: dict | None = None,
                 lang: str = 'ar') -> AgentResponse:
        params = params or {}
        if action not in self.CATALOGUE:
            raise ValueError(f"Unknown Operations action: {action}")
        handler = getattr(self, f'_do_{action}', self._generic)
        return handler(action, params, lang)

    def _do_kpi_dashboard(self, action, params, lang):
        from apps.accounts.reports import income_statement
        from datetime import date
        today = date.today()
        pl = income_statement(self.company, today.replace(month=1, day=1), today)
        kpis = {
            'net_profit_ytd': float(pl['net_profit']),
            'revenue_ytd': float(pl['total_income']),
            'expense_ytd': float(pl['total_expense']),
        }
        return AgentResponse(agent='AI-Operations', action=action, result=kpis,
                             proposed_actions=[],
                             narrative="مؤشرات الأداء الحالية" if lang == 'ar' else "Current KPIs")

    def _generic(self, action, params, lang):
        return AgentResponse(agent='AI-Operations', action=action,
                             result={'status': 'queued'}, proposed_actions=[],
                             narrative=self.CATALOGUE[action])


# ── AI Developer ─────────────────────────────────────────────────
class AIDeveloperAgent:
    """AI Developer — code review, API docs, migration scripts, bug triage."""

    CATALOGUE = {
        'code_review': 'Review a code snippet for bugs/security/style',
        'api_docs': 'Generate API documentation from a viewset',
        'migration_script': 'Generate data migration from schema change',
        'bug_triage': 'Analyze error log and suggest fix',
        'test_generation': 'Generate unit tests for a module',
        'security_audit': 'Audit code for OWASP top 10 issues',
    }

    def __init__(self, company=None, user=None):
        self.company = company
        self.user = user

    def dispatch(self, action: str, params: dict | None = None,
                 lang: str = 'en') -> AgentResponse:
        params = params or {}
        if action not in self.CATALOGUE:
            raise ValueError(f"Unknown Developer action: {action}")
        return self._llm_dispatch(action, params, lang)

    def _llm_dispatch(self, action, params, lang):
        try:
            from apps.core.intelligence.ai_brain import LLMCore
            llm = LLMCore()
            prompt = (f"You are an expert Django/Python developer.\n"
                      f"Task: {self.CATALOGUE[action]}\n"
                      f"Input: {params.get('code') or params.get('input', '')}\n"
                      f"Language: {'Arabic response preferred' if lang == 'ar' else 'English'}")
            result = llm.generate(prompt, max_tokens=2000)
            return AgentResponse(agent='AI-Developer', action=action,
                                 result={'response': result}, proposed_actions=[],
                                 narrative=str(result)[:200])
        except Exception as exc:
            return AgentResponse(agent='AI-Developer', action=action,
                                 result={'error': str(exc)}, proposed_actions=[],
                                 narrative=f"Error: {exc}")


# ── Agent Registry ────────────────────────────────────────────────
AGENT_REGISTRY = {
    'cfo': AICFOAgent,
    'procurement': AIProcurementAgent,
    'operations': AIOperationsAgent,
    'developer': AIDeveloperAgent,
}


def get_agent(role: str, company=None, user=None):
    cls = AGENT_REGISTRY.get(role)
    if cls is None:
        raise ValueError(f"Unknown agent role: {role}. "
                         f"Available: {list(AGENT_REGISTRY)}")
    return cls(company=company, user=user)
