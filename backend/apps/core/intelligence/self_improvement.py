"""
Self-Improvement Layer for Nexus CE-ERP OS
Monitors system, analyzes patterns, suggests improvements, controls deployment
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

from apps.core.intelligence.ai_brain import llm_core, rag_memory
from apps.core.runtime.event_bus import event_bus, DomainEvent, EventTypes, EventPriority

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    RULE_ADJUSTMENT = "rule_adjustment"
    AUTOMATION_ADDITION = "automation_addition"
    UI_ENHANCEMENT = "ui_enhancement"
    PERFORMANCE_TUNING = "performance_tuning"
    SECURITY_HARDENING = "security_hardening"
    DATA_QUALITY = "data_quality"


class ImprovementStatus(Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    SUGGESTED = "suggested"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


@dataclass
class SystemMetric:
    metric_name: str
    value: float
    unit: str
    timestamp: str
    tags: Dict[str, str]
    threshold: Optional[float] = None


class MonitoringLayer:
    """Collects and analyzes system metrics"""

    def __init__(self):
        self.metrics_buffer = []
        self.anomaly_threshold = 2.0  # Standard deviations

    def collect_metric(self, metric: SystemMetric):
        """Collect a system metric"""
        self.metrics_buffer.append(metric)

        # Check for threshold violations
        if metric.threshold and metric.value > metric.threshold:
            self._alert_threshold_violation(metric)

        # Keep buffer size manageable
        if len(self.metrics_buffer) > 10000:
            self.metrics_buffer = self.metrics_buffer[-5000:]

    def _alert_threshold_violation(self, metric: SystemMetric):
        """Alert when metric exceeds threshold"""
        event = DomainEvent.create(
            event_type=EventTypes.AI_ANOMALY_DETECTED,
            aggregate_type="metric",
            aggregate_id=metric.metric_name,
            tenant_id=metric.tags.get('tenant_id', ''),
            payload={
                'metric_name': metric.metric_name,
                'value': metric.value,
                'threshold': metric.threshold,
                'severity': 'warning' if metric.value < metric.threshold * 1.5 else 'critical'
            },
            priority=EventPriority.HIGH
        )
        event_bus.publish(event)

    def analyze_trends(self, metric_name: str, hours: int = 24) -> Dict:
        """Analyze trends for a specific metric"""
        cutoff = datetime.now() - timedelta(hours=hours)
        relevant = [m for m in self.metrics_buffer 
                     if m.metric_name == metric_name and 
                     datetime.fromisoformat(m.timestamp) > cutoff]

        if not relevant:
            return {'trend': 'insufficient_data', 'change_percent': 0}

        values = [m.value for m in relevant]
        avg = sum(values) / len(values)

        # Simple trend analysis
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        if not first_half or not second_half:
            return {'trend': 'insufficient_data', 'change_percent': 0}

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if first_avg == 0:
            change_pct = 0
        else:
            change_pct = ((second_avg - first_avg) / first_avg) * 100

        trend = 'stable'
        if change_pct > 10:
            trend = 'increasing'
        elif change_pct < -10:
            trend = 'decreasing'

        return {
            'trend': trend,
            'change_percent': round(change_pct, 2),
            'average': round(avg, 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'sample_count': len(values)
        }

    def detect_bottlenecks(self) -> List[Dict]:
        """Detect workflow and system bottlenecks"""
        bottlenecks = []

        # Analyze workflow completion times
        workflow_times = self._get_workflow_metrics()
        avg_time = sum(workflow_times) / len(workflow_times) if workflow_times else 0

        for i, time in enumerate(workflow_times):
            if time > avg_time * 2:
                bottlenecks.append({
                    'type': 'workflow_slow',
                    'workflow_id': i,
                    'completion_time': time,
                    'average_time': avg_time,
                    'severity': 'high' if time > avg_time * 3 else 'medium'
                })

        # Analyze error rates
        error_rates = self._get_error_metrics()
        for module, rate in error_rates.items():
            if rate > 0.05:  # 5% error rate
                bottlenecks.append({
                    'type': 'high_error_rate',
                    'module': module,
                    'error_rate': rate,
                    'severity': 'critical' if rate > 0.1 else 'high'
                })

        return bottlenecks

    def _get_workflow_metrics(self) -> List[float]:
        """Get workflow completion times from metrics"""
        return [m.value for m in self.metrics_buffer 
                if m.metric_name == 'workflow_completion_time']

    def _get_error_metrics(self) -> Dict[str, float]:
        """Get error rates by module"""
        errors = {}
        for m in self.metrics_buffer:
            if m.metric_name == 'error_rate':
                module = m.tags.get('module', 'unknown')
                errors[module] = m.value
        return errors


class AIAnalyzer:
    """AI-powered analysis of system patterns"""

    def __init__(self, llm=None):
        self.llm = llm or llm_core

    def analyze_workflows(self, workflow_data: List[Dict]) -> Dict:
        """Analyze workflow patterns for optimization opportunities"""
        prompt = f"""Analyze these workflow execution patterns:
{json.dumps(workflow_data[:50], indent=2)}

Identify:
1. Slowest workflow steps
2. Most common failure points
3. Redundant steps
4. Parallelization opportunities
5. Automation candidates

Provide structured analysis with specific recommendations.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'analysis': response['text'],
            'timestamp': datetime.now().isoformat()
        }

    def analyze_errors(self, error_logs: List[Dict]) -> Dict:
        """Analyze error patterns"""
        prompt = f"""Analyze these error patterns:
{json.dumps(error_logs[:50], indent=2)}

Identify:
1. Most frequent errors
2. Root cause categories
3. Affected modules
4. User impact
5. Fix priorities

Provide structured analysis.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'analysis': response['text'],
            'timestamp': datetime.now().isoformat()
        }

    def analyze_user_behavior(self, user_activity: List[Dict]) -> Dict:
        """Analyze user behavior for UX improvements"""
        prompt = f"""Analyze user behavior patterns:
{json.dumps(user_activity[:50], indent=2)}

Identify:
1. Most/least used features
2. Common navigation paths
3. Friction points
4. Feature adoption rates
5. Training needs

Provide UX improvement recommendations.
"""

        response = self.llm.generate(prompt=prompt)
        return {
            'analysis': response['text'],
            'timestamp': datetime.now().isoformat()
        }


class SuggestionEngine:
    """Generates improvement suggestions based on analysis"""

    def __init__(self, llm=None):
        self.llm = llm or llm_core

    def generate_suggestion(self, analysis: Dict, improvement_type: ImprovementType) -> Dict:
        """Generate a specific improvement suggestion"""
        prompt = f"""Based on this analysis:
{json.dumps(analysis, indent=2)}

Generate a specific improvement suggestion of type: {improvement_type.value}

The suggestion must include:
1. Title
2. Description
3. Expected impact (quantified if possible)
4. Implementation steps
5. Risk assessment
6. Rollback plan

Format as JSON.
"""

        response = self.llm.generate(prompt=prompt)

        try:
            suggestion = json.loads(response['text'])
        except:
            suggestion = {
                'title': f'Improvement: {improvement_type.value}',
                'description': response['text'],
                'expected_impact': 'Unknown',
                'implementation_steps': [],
                'risk': 'low',
                'rollback_plan': 'Revert configuration'
            }

        return {
            'suggestion': suggestion,
            'type': improvement_type.value,
            'confidence': 0.75,
            'timestamp': datetime.now().isoformat()
        }

    def prioritize_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Prioritize suggestions by impact and effort"""
        # Simple scoring: impact / effort
        for s in suggestions:
            impact = self._score_impact(s.get('suggestion', {}).get('expected_impact', ''))
            effort = self._score_effort(s.get('suggestion', {}).get('implementation_steps', []))
            s['priority_score'] = impact / max(effort, 1)

        return sorted(suggestions, key=lambda x: x['priority_score'], reverse=True)

    def _score_impact(self, impact_text: str) -> float:
        """Score impact from text"""
        impact_text = impact_text.lower()
        if 'high' in impact_text or 'critical' in impact_text:
            return 5.0
        elif 'medium' in impact_text:
            return 3.0
        elif 'low' in impact_text:
            return 1.0
        return 2.5

    def _score_effort(self, steps: List) -> float:
        """Score effort from implementation steps"""
        count = len(steps)
        if count <= 2:
            return 1.0
        elif count <= 5:
            return 2.0
        elif count <= 10:
            return 3.5
        return 5.0


class ControlledDeployment:
    """Manages controlled deployment of improvements with human approval"""

    def __init__(self):
        self.pending_deployments = {}

    def propose_deployment(self, suggestion: Dict, proposed_by: str = "AI") -> str:
        """Propose an improvement for human approval"""
        deployment_id = str(uuid.uuid4())

        deployment = {
            'id': deployment_id,
            'suggestion': suggestion,
            'status': ImprovementStatus.PENDING_APPROVAL.value,
            'proposed_by': proposed_by,
            'proposed_at': datetime.now().isoformat(),
            'approved_by': None,
            'approved_at': None,
            'deployed_at': None,
            'rolled_back_at': None,
            'version': self._get_next_version()
        }

        self.pending_deployments[deployment_id] = deployment

        # Publish event for approval workflow
        event = DomainEvent.create(
            event_type=EventTypes.AI_SUGGESTION_GENERATED,
            aggregate_type="improvement",
            aggregate_id=deployment_id,
            tenant_id='',
            payload={
                'title': suggestion.get('suggestion', {}).get('title', ''),
                'type': suggestion.get('type', ''),
                'requires_approval': True
            },
            priority=EventPriority.HIGH
        )
        event_bus.publish(event)

        return deployment_id

    def approve_deployment(self, deployment_id: str, approved_by: str) -> bool:
        """Human approves deployment"""
        deployment = self.pending_deployments.get(deployment_id)
        if not deployment:
            return False

        deployment['status'] = ImprovementStatus.APPROVED.value
        deployment['approved_by'] = approved_by
        deployment['approved_at'] = datetime.now().isoformat()

        logger.info(f"Improvement {deployment_id} approved by {approved_by}")
        return True

    def deploy(self, deployment_id: str) -> Dict:
        """Deploy approved improvement"""
        deployment = self.pending_deployments.get(deployment_id)
        if not deployment:
            return {'success': False, 'error': 'Deployment not found'}

        if deployment['status'] != ImprovementStatus.APPROVED.value:
            return {'success': False, 'error': 'Deployment not approved'}

        try:
            # Execute deployment
            result = self._execute_deployment(deployment)

            deployment['status'] = ImprovementStatus.DEPLOYED.value
            deployment['deployed_at'] = datetime.now().isoformat()

            return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {'success': False, 'error': str(e)}

    def rollback(self, deployment_id: str) -> bool:
        """Rollback a deployed improvement"""
        deployment = self.pending_deployments.get(deployment_id)
        if not deployment:
            return False

        try:
            # Execute rollback
            self._execute_rollback(deployment)

            deployment['status'] = ImprovementStatus.ROLLED_BACK.value
            deployment['rolled_back_at'] = datetime.now().isoformat()

            logger.info(f"Improvement {deployment_id} rolled back")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _execute_deployment(self, deployment: Dict) -> Dict:
        """Execute the actual deployment"""
        suggestion = deployment['suggestion']
        impl_type = suggestion.get('type', '')

        # This would integrate with the actual system
        # For now, log the intended changes
        logger.info(f"Deploying improvement: {impl_type}")
        return {'status': 'deployed', 'changes': suggestion.get('suggestion', {}).get('implementation_steps', [])}

    def _execute_rollback(self, deployment: Dict):
        """Execute rollback"""
        logger.info(f"Rolling back deployment: {deployment['id']}")

    def _get_next_version(self) -> str:
        """Get next version number"""
        return "1.0.0"  # Simplified


# ============================================================
# Models for Self-Improvement
# ============================================================

class SystemImprovement(models.Model):
    """Tracks proposed and deployed system improvements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    improvement_type = models.CharField(max_length=50, choices=[
        (t.value, t.value.replace('_', ' ').title()) for t in ImprovementType
    ])
    status = models.CharField(max_length=50, choices=[
        (s.value, s.value.replace('_', ' ').title()) for s in ImprovementStatus
    ], default=ImprovementStatus.DETECTED.value)

    analysis_data = models.JSONField(default=dict)
    suggestion_data = models.JSONField(default=dict)
    expected_impact = models.TextField(blank=True)
    implementation_steps = models.JSONField(default=list)
    risk_assessment = models.TextField(blank=True)
    rollback_plan = models.TextField(blank=True)

    proposed_by = models.CharField(max_length=100, default="AI")
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    deployed_at = models.DateTimeField(null=True, blank=True)
    rolled_back_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class PerformanceMetric(models.Model):
    """Stores performance metrics for trend analysis"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=dict)
    threshold = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['metric_name', 'recorded_at']),
            models.Index(fields=['tags']),
        ]


# Global instances
monitoring_layer = MonitoringLayer()
ai_analyzer = AIAnalyzer()
suggestion_engine = SuggestionEngine()
controlled_deployment = ControlledDeployment()
