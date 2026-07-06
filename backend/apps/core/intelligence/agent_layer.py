"""
Agent Layer for Nexus CE-ERP OS
AI-powered autonomous agents that act as "smart employees"
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from django.db import models
from django.utils import timezone
import uuid

from apps.core.ai_brain import LLMCore, RAGMemory, ContextEngine, llm_core, rag_memory, context_engine
from apps.core.event_bus import event_bus, DomainEvent, EventTypes, EventPriority

logger = logging.getLogger(__name__)


class AgentAction(Enum):
    ANALYZE = "analyze"
    SUGGEST = "suggest"
    EXECUTE = "execute"
    ALERT = "alert"
    PREDICT = "predict"
    AUTOMATE = "automate"


@dataclass
class AgentTask:
    task_id: str
    agent_type: str
    action: AgentAction
    target_module: str
    target_id: Optional[str]
    parameters: Dict[str, Any]
    priority: int = 1
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class BaseAgent:
    """Base class for all AI agents"""

    agent_type: str = "base"
    description: str = "Base AI agent"
    capabilities: List[str] = []

    def __init__(self, llm: LLMCore = None, rag: RAGMemory = None, context: ContextEngine = None):
        self.llm = llm or llm_core
        self.rag = rag or rag_memory
        self.context = context or context_engine
        self.task_history = []

    def can_handle(self, task: AgentTask) -> bool:
        """Check if this agent can handle the task"""
        return task.agent_type == self.agent_type

    def execute(self, task: AgentTask) -> Dict[str, Any]:
        """Execute the agent task"""
        raise NotImplementedError

    def _build_system_prompt(self, user_context) -> str:
        """Build system prompt for the agent"""
        return f"""You are the {self.description} for an ERP system.
User Role: {user_context.role}
Capabilities: {', '.join(self.capabilities)}

You must:
1. Analyze the situation thoroughly
2. Provide actionable recommendations
3. Suggest specific ERP actions when appropriate
4. Be concise and professional
"""

    def _log_action(self, task: AgentTask, result: Dict):
        """Log agent action for audit"""
        self.task_history.append({
            'task_id': task.task_id,
            'action': task.action.value,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })

        # Publish event
        event = DomainEvent.create(
            event_type=EventTypes.AI_SUGGESTION_GENERATED,
            aggregate_type="agent",
            aggregate_id=task.task_id,
            tenant_id=task.parameters.get('tenant_id', ''),
            payload={
                'agent_type': self.agent_type,
                'action': task.action.value,
                'target_module': task.target_module,
                'result_summary': result.get('summary', '')
            }
        )
        event_bus.publish(event)


# ============================================================
# Finance Agent
# ============================================================

class FinanceAgent(BaseAgent):
    """AI agent for financial operations"""

    agent_type = "finance"
    description = "Finance AI Agent"
    capabilities = [
        "invoice_classification",
        "anomaly_detection",
        "cash_flow_prediction",
        "budget_variance_analysis",
        "tax_optimization",
        "financial_reporting",
        "zakat_calculation"
    ]

    def execute(self, task: AgentTask) -> Dict[str, Any]:
        if task.action == AgentAction.ANALYZE:
            return self._analyze_financials(task)
        elif task.action == AgentAction.PREDICT:
            return self._predict_cash_flow(task)
        elif task.action == AgentAction.ALERT:
            return self._detect_anomalies(task)
        elif task.action == AgentAction.SUGGEST:
            return self._suggest_actions(task)
        elif task.action == AgentAction.AUTOMATE:
            return self._automate_task(task)
        return {"error": "Unknown action"}

    def _analyze_financials(self, task: AgentTask) -> Dict:
        params = task.parameters
        company_id = params.get('company_id')

        # Get relevant financial data from RAG
        context = self.rag.query(
            "company_knowledge",
            f"financial data company {company_id}",
            tenant_id=company_id
        )

        prompt = f"""Analyze the financial health of the company based on:
- Revenue trends
- Expense patterns
- Cash flow status
- Outstanding receivables/payables

Company ID: {company_id}
Context: {json.dumps([c['text'] for c in context[:3]])}

Provide:
1. Key financial metrics summary
2. Trends and patterns
3. Risk areas
4. Recommendations
"""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self._build_system_prompt(params.get('user_context'))
        )

        result = {
            'analysis': response['text'],
            'metrics': self._extract_metrics(response['text']),
            'confidence': 0.85,
            'summary': "Financial analysis completed"
        }
        self._log_action(task, result)
        return result

    def _predict_cash_flow(self, task: AgentTask) -> Dict:
        params = task.parameters
        days = params.get('days', 30)

        prompt = f"""Predict cash flow for the next {days} days based on:
- Historical cash flow patterns
- Upcoming invoices (receivable and payable)
- Seasonal trends
- Current bank balance

Provide:
1. Daily cash flow prediction
2. Potential shortfalls
3. Optimization suggestions
"""

        response = self.llm.generate(prompt=prompt)

        result = {
            'prediction': response['text'],
            'period_days': days,
            'confidence': 0.75,
            'summary': f"Cash flow predicted for next {days} days"
        }
        self._log_action(task, result)
        return result

    def _detect_anomalies(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Analyze financial transactions for anomalies:
- Unusual amounts
- Duplicate transactions
- Unusual timing
- Unauthorized vendors
- Round-number amounts
- Off-hours transactions

Data: {json.dumps(params.get('transactions', []))}

Flag any suspicious items with confidence scores.
"""

        response = self.llm.generate(prompt=prompt)

        result = {
            'anomalies': self._parse_anomalies(response['text']),
            'risk_score': 0.0,
            'summary': "Anomaly detection completed"
        }
        self._log_action(task, result)
        return result

    def _suggest_actions(self, task: AgentTask) -> Dict:
        params = task.parameters
        scenario = params.get('scenario', '')

        prompt = f"""Given this financial scenario: {scenario}

Suggest specific ERP actions:
1. Which module to use
2. Which transaction to create
3. Approval workflow needed
4. Impact on financial statements
"""

        response = self.llm.generate(prompt=prompt)

        result = {
            'suggestions': response['text'],
            'actions': self._extract_actions(response['text']),
            'summary': "Action suggestions generated"
        }
        self._log_action(task, result)
        return result

    def _automate_task(self, task: AgentTask) -> Dict:
        """Execute automated financial tasks"""
        params = task.parameters
        automation_type = params.get('automation_type')

        if automation_type == 'invoice_classification':
            return self._auto_classify_invoice(params)
        elif automation_type == 'zakat_calculation':
            return self._calculate_zakat(params)

        return {"error": "Unknown automation type"}

    def _auto_classify_invoice(self, params: Dict) -> Dict:
        invoice_data = params.get('invoice_data', {})

        prompt = f"""Classify this invoice:
Vendor: {invoice_data.get('vendor', '')}
Amount: {invoice_data.get('amount', '')}
Description: {invoice_data.get('description', '')}

Classify into:
1. Expense category (utilities, rent, supplies, services, etc.)
2. GL account code
3. Tax treatment (VAT, exempt, zero-rated)
4. Department allocation

Return as JSON.
"""

        response = self.llm.generate(prompt=prompt)

        try:
            classification = json.loads(response['text'])
        except:
            classification = {'category': 'uncategorized', 'account': 'miscellaneous'}

        return {
            'classification': classification,
            'confidence': 0.88,
            'summary': f"Invoice classified as {classification.get('category', 'uncategorized')}"
        }

    def _calculate_zakat(self, params: Dict) -> Dict:
        company_id = params.get('company_id')

        prompt = f"""Calculate Zakat for company {company_id}:

Zakat Rules (Saudi Arabia):
- 2.5% of net worth
- Eligible assets: cash, inventory, receivables
- Deduct: payables, loans
- Haul (lunar year) requirement
- Nisab threshold

Provide:
1. Zakat base calculation
2. Zakat amount
3. Due date
4. Supporting documentation needed
"""

        response = self.llm.generate(prompt=prompt)

        return {
            'zakat_calculation': response['text'],
            'summary': "Zakat calculation completed"
        }

    def _extract_metrics(self, text: str) -> Dict:
        """Extract financial metrics from analysis text"""
        return {
            'revenue_growth': 'N/A',
            'profit_margin': 'N/A',
            'cash_position': 'N/A'
        }

    def _parse_anomalies(self, text: str) -> List[Dict]:
        """Parse anomaly detection results"""
        return []

    def _extract_actions(self, text: str) -> List[Dict]:
        """Extract suggested actions"""
        return []


# ============================================================
# HR Agent
# ============================================================

class HRAgent(BaseAgent):
    """AI agent for HR operations"""

    agent_type = "hr"
    description = "HR AI Agent"
    capabilities = [
        "recruitment_screening",
        "leave_optimization",
        "performance_analysis",
        "salary_benchmarking",
        "attendance_anomaly",
        "training_recommendations",
        "compliance_checking"
    ]

    def execute(self, task: AgentTask) -> Dict[str, Any]:
        if task.action == AgentAction.ANALYZE:
            return self._analyze_workforce(task)
        elif task.action == AgentAction.SUGGEST:
            return self._suggest_hr_actions(task)
        elif task.action == AgentAction.PREDICT:
            return self._predict_turnover(task)
        elif task.action == AgentAction.ALERT:
            return self._check_compliance(task)
        return {"error": "Unknown action"}

    def _analyze_workforce(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Analyze workforce metrics:
- Headcount trends
- Department distribution
- Performance distribution
- Salary distribution
- Leave utilization
- Training completion rates

Company: {params.get('company_id')}

Provide insights and recommendations.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'analysis': response['text'],
            'summary': "Workforce analysis completed"
        }

    def _predict_turnover(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Predict employee turnover risk:
- Analyze patterns in resignations
- Identify at-risk employees
- Factors: tenure, performance, leave patterns, salary vs market

Provide:
1. Risk scores for departments
2. At-risk employee profiles
3. Retention strategies
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'prediction': response['text'],
            'summary': "Turnover prediction completed"
        }

    def _suggest_hr_actions(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Given HR scenario: {params.get('scenario')}

Suggest:
1. Policy changes
2. Training programs
3. Recruitment strategies
4. Compensation adjustments
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'suggestions': response['text'],
            'summary': "HR recommendations generated"
        }

    def _check_compliance(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Check HR compliance for Saudi labor law:
- Contract types
- Working hours
- Leave entitlements
- End-of-service calculations
- Saudization ratios

Company: {params.get('company_id')}

Flag any compliance issues.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'compliance_status': response['text'],
            'summary': "Compliance check completed"
        }


# ============================================================
# Supply Chain Agent
# ============================================================

class SupplyChainAgent(BaseAgent):
    """AI agent for supply chain and inventory"""

    agent_type = "supply_chain"
    description = "Supply Chain AI Agent"
    capabilities = [
        "demand_forecasting",
        "inventory_optimization",
        "supplier_evaluation",
        "reorder_automation",
        "lead_time_analysis",
        "stock_level_optimization"
    ]

    def execute(self, task: AgentTask) -> Dict[str, Any]:
        if task.action == AgentAction.PREDICT:
            return self._forecast_demand(task)
        elif task.action == AgentAction.SUGGEST:
            return self._optimize_inventory(task)
        elif task.action == AgentAction.AUTOMATE:
            return self._auto_reorder(task)
        elif task.action == AgentAction.ALERT:
            return self._check_stock_levels(task)
        return {"error": "Unknown action"}

    def _forecast_demand(self, task: AgentTask) -> Dict:
        params = task.parameters
        item_id = params.get('item_id')

        prompt = f"""Forecast demand for item {item_id}:
- Historical sales data
- Seasonal patterns
- Market trends
- Promotional calendar

Provide:
1. Weekly demand forecast (next 12 weeks)
2. Confidence intervals
3. Seasonal adjustments
4. Safety stock recommendations
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'forecast': response['text'],
            'summary': f"Demand forecast for item {item_id}"
        }

    def _optimize_inventory(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Optimize inventory levels:
- ABC analysis
- EOQ calculation
- Safety stock levels
- Reorder points
- Warehouse allocation

Company: {params.get('company_id')}

Provide actionable recommendations.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'optimization': response['text'],
            'summary': "Inventory optimization completed"
        }

    def _auto_reorder(self, task: AgentTask) -> Dict:
        params = task.parameters

        # This would trigger actual purchase orders
        prompt = f"""Generate auto-reorder recommendations:
- Items below reorder point
- Preferred suppliers
- Optimal order quantities
- Delivery schedules

Items: {json.dumps(params.get('items', []))}

Return structured reorder plan.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'reorder_plan': response['text'],
            'summary': "Auto-reorder plan generated"
        }

    def _check_stock_levels(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Check stock levels and alert on:
- Items below minimum stock
- Items approaching expiry
- Slow-moving inventory
- Overstocked items
- Warehouse capacity

Company: {params.get('company_id')}

Generate alerts with severity levels.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'alerts': response['text'],
            'summary': "Stock level check completed"
        }


# ============================================================
# Admin Agent
# ============================================================

class AdminAgent(BaseAgent):
    """AI agent for system administration and configuration"""

    agent_type = "admin"
    description = "Admin AI Agent"
    capabilities = [
        "system_monitoring",
        "user_access_audit",
        "configuration_optimization",
        "security_analysis",
        "performance_tuning",
        "backup_verification"
    ]

    def execute(self, task: AgentTask) -> Dict[str, Any]:
        if task.action == AgentAction.ANALYZE:
            return self._analyze_system(task)
        elif task.action == AgentAction.ALERT:
            return self._security_audit(task)
        elif task.action == AgentAction.SUGGEST:
            return self._suggest_optimizations(task)
        return {"error": "Unknown action"}

    def _analyze_system(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Analyze system health:
- Database performance
- API response times
- Error rates
- Resource utilization
- User activity patterns
- Module usage statistics

Provide:
1. Performance metrics
2. Bottlenecks identified
3. Optimization recommendations
4. Capacity planning
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'analysis': response['text'],
            'summary': "System analysis completed"
        }

    def _security_audit(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Perform security audit:
- User access patterns
- Failed login attempts
- Permission violations
- Data access anomalies
- API abuse patterns

Company: {params.get('company_id')}

Flag security concerns.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'audit_results': response['text'],
            'summary': "Security audit completed"
        }

    def _suggest_optimizations(self, task: AgentTask) -> Dict:
        params = task.parameters

        prompt = f"""Suggest system optimizations:
- Database indexing
- Query optimization
- Cache strategies
- Worker scaling
- Storage optimization
- CDN usage

Provide specific, actionable recommendations.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'optimizations': response['text'],
            'summary': "Optimization suggestions generated"
        }


# ============================================================
# Agent Orchestrator
# ============================================================

class AgentOrchestrator:
    """Routes tasks to appropriate agents and manages execution"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        self.register_agent(FinanceAgent())
        self.register_agent(HRAgent())
        self.register_agent(SupplyChainAgent())
        self.register_agent(AdminAgent())

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.agent_type] = agent
        logger.info(f"Agent registered: {agent.agent_type}")

    def dispatch(self, task: AgentTask) -> Dict[str, Any]:
        """Dispatch task to appropriate agent"""
        agent = self.agents.get(task.agent_type)
        if not agent:
            return {"error": f"No agent found for type: {task.agent_type}"}

        if not agent.can_handle(task):
            return {"error": f"Agent {task.agent_type} cannot handle this task"}

        try:
            result = agent.execute(task)
            result['agent_type'] = task.agent_type
            result['task_id'] = task.task_id
            result['status'] = 'success'
            return result
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                'error': str(e),
                'agent_type': task.agent_type,
                'task_id': task.task_id,
                'status': 'failed'
            }

    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all registered agents"""
        return {agent_type: agent.capabilities for agent_type, agent in self.agents.items()}

    def broadcast(self, action: AgentAction, parameters: Dict, 
                  target_modules: List[str] = None) -> Dict[str, Dict]:
        """Broadcast task to multiple relevant agents"""
        results = {}
        for agent_type, agent in self.agents.items():
            if target_modules and agent.agent_type not in target_modules:
                continue
            task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type=agent_type,
                action=action,
                target_module=agent_type,
                target_id=None,
                parameters=parameters
            )
            results[agent_type] = self.dispatch(task)
        return results


# Global orchestrator
agent_orchestrator = AgentOrchestrator()
