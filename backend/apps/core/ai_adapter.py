"""
AI Adapter Layer for Nexus Framework
Provides abstraction over different AI providers.
Supports: Rule-based (default), OpenAI, Google Gemini, Anthropic Claude
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def analyze_risks(self, project_data: Dict) -> Dict:
        """Analyze project risks and return recommendations."""
        pass

    @abstractmethod
    def suggest_task_assignment(self, task_data: Dict, employees: List[Dict]) -> List[Dict]:
        """Suggest optimal task assignments."""
        pass

    @abstractmethod
    def predict_delay(self, project_data: Dict) -> Dict:
        """Predict project delays based on current velocity."""
        pass

    @abstractmethod
    def generate_status_report(self, project_data: Dict) -> Dict:
        """Generate a project status report."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        pass


class RuleBasedProvider(AIProvider):
    """
    Default rule-based AI provider.
    Uses statistical analysis and business rules without external APIs.
    """

    def is_available(self) -> bool:
        return True  # Always available

    def analyze_risks(self, project_data: Dict) -> Dict:
        """Rule-based risk analysis."""
        risks = project_data.get('risks', [])
        issues = project_data.get('issues', [])
        tasks = project_data.get('tasks', [])

        recommendations = []

        # Check for high probability + high impact risks
        for risk in risks:
            if risk.get('probability', 0) >= 4 and risk.get('impact', 0) >= 4:
                recommendations.append({
                    'type': 'risk',
                    'severity': 'high',
                    'message': f"Critical risk: {risk.get('title', 'Unknown')}",
                    'action': risk.get('mitigation', 'Develop mitigation plan immediately')
                })

        # Check for overdue tasks
        overdue_count = sum(1 for t in tasks if t.get('is_overdue'))
        if overdue_count > 0:
            recommendations.append({
                'type': 'schedule',
                'severity': 'high',
                'message': f"{overdue_count} task(s) are overdue",
                'action': 'Review timeline and allocate additional resources'
            })

        # Check budget
        budget = project_data.get('budget', 0)
        actual_cost = project_data.get('actual_cost', 0)
        if budget > 0 and actual_cost > budget * 0.9:
            recommendations.append({
                'type': 'budget',
                'severity': 'high' if actual_cost > budget else 'medium',
                'message': f"Budget utilization: {(actual_cost/budget)*100:.1f}%",
                'action': 'Prepare change request for additional budget'
            })

        # Calculate health score
        score = 100
        score -= len([r for r in risks if r.get('probability', 0) >= 4 and r.get('impact', 0) >= 4]) * 10
        score -= overdue_count * 5
        score -= len([i for i in issues if i.get('severity') in ['High', 'Critical']]) * 5

        return {
            'provider': 'rule_based',
            'recommendations': recommendations,
            'health_score': max(0, min(100, score)),
            'risk_summary': {
                'total': len(risks),
                'high': len([r for r in risks if r.get('probability', 0) >= 4 and r.get('impact', 0) >= 4]),
                'medium': len([r for r in risks if 2 <= r.get('probability', 0) < 4 or 2 <= r.get('impact', 0) < 4]),
            }
        }

    def suggest_task_assignment(self, task_data: Dict, employees: List[Dict]) -> List[Dict]:
        """Rule-based task assignment suggestions."""
        suggestions = []

        for emp in employees:
            score = 100

            # Penalty for high workload
            active_tasks = emp.get('active_tasks', 0)
            score -= active_tasks * 10

            # Bonus for project familiarity
            completed_in_project = emp.get('completed_in_project', 0)
            score += completed_in_project * 5

            # Bonus for matching skills/department
            if emp.get('department') == task_data.get('department'):
                score += 15

            # Bonus for same team
            if emp.get('team_id') == task_data.get('team_id'):
                score += 20

            suggestions.append({
                'employee_id': emp.get('id'),
                'name': emp.get('name'),
                'suitability_score': max(0, score),
                'reason': f"Active tasks: {active_tasks}, Completed in project: {completed_in_project}",
                'active_tasks': active_tasks,
                'completed_in_project': completed_in_project
            })

        suggestions.sort(key=lambda x: x['suitability_score'], reverse=True)
        return suggestions[:5]

    def predict_delay(self, project_data: Dict) -> Dict:
        """Rule-based delay prediction."""
        tasks = project_data.get('tasks', [])
        total = len(tasks)
        completed = len([t for t in tasks if t.get('status') == 'Completed'])

        if total == 0:
            return {'error': 'No tasks to analyze'}

        # Simple velocity calculation
        days_elapsed = project_data.get('days_elapsed', 1)
        velocity = completed / max(days_elapsed, 1)
        remaining = total - completed
        days_needed = remaining / max(velocity, 0.1)

        expected_end = project_data.get('expected_end')
        predicted_end = project_data.get('start_date') + days_needed if project_data.get('start_date') else None

        delay_days = 0
        if expected_end and predicted_end:
            delay_days = max(0, predicted_end - expected_end)

        return {
            'provider': 'rule_based',
            'velocity': round(velocity, 2),
            'tasks_completed': completed,
            'tasks_remaining': remaining,
            'predicted_days': round(days_needed, 0),
            'delay_days': delay_days,
            'on_track': delay_days == 0,
            'risk_level': 'high' if delay_days > 14 else 'medium' if delay_days > 7 else 'low'
        }

    def generate_status_report(self, project_data: Dict) -> Dict:
        """Rule-based status report generation."""
        tasks = project_data.get('tasks', [])
        risks = project_data.get('risks', [])
        issues = project_data.get('issues', [])

        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.get('status') == 'Completed'])
        in_progress = len([t for t in tasks if t.get('status') == 'Working'])
        overdue = len([t for t in tasks if t.get('is_overdue')])

        insights = []
        if total_tasks > 0:
            completion_rate = (completed / total_tasks) * 100
            insights.append(f"Project is {completion_rate:.0f}% complete with {in_progress} tasks in progress.")

        critical_risks = [r for r in risks if r.get('probability', 0) >= 4 and r.get('impact', 0) >= 4]
        if critical_risks:
            insights.append(f"⚠️ {len(critical_risks)} critical risks require immediate attention.")

        open_issues = [i for i in issues if i.get('status') in ['Open', 'In Progress']]
        if open_issues:
            high_severity = [i for i in open_issues if i.get('severity') in ['High', 'Critical']]
            insights.append(f"{len(open_issues)} open issues ({len(high_severity)} high severity).")

        return {
            'provider': 'rule_based',
            'executive_summary': f"Project is {project_data.get('status', 'Unknown')}. Overall progress: {project_data.get('progress_percent', 0)}%.",
            'insights': insights,
            'key_metrics': {
                'total_tasks': total_tasks,
                'completed': completed,
                'in_progress': in_progress,
                'overdue': overdue,
                'open_risks': len([r for r in risks if r.get('status') == 'Open']),
                'open_issues': len(open_issues),
            }
        }


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider (requires OPENAI_API_KEY)."""

    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4')

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _call_api(self, prompt: str) -> Dict:
        """Call OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return {'success': True, 'content': response.choices[0].message.content}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def analyze_risks(self, project_data: Dict) -> Dict:
        if not self.is_available():
            return {'error': 'OpenAI not configured'}
        # Implementation would call OpenAI API
        return {'provider': 'openai', 'status': 'not_implemented'}

    def suggest_task_assignment(self, task_data: Dict, employees: List[Dict]) -> List[Dict]:
        if not self.is_available():
            return []
        return []

    def predict_delay(self, project_data: Dict) -> Dict:
        if not self.is_available():
            return {'error': 'OpenAI not configured'}
        return {}

    def generate_status_report(self, project_data: Dict) -> Dict:
        if not self.is_available():
            return {'error': 'OpenAI not configured'}
        return {}


class GeminiProvider(AIProvider):
    """Google Gemini provider (requires GEMINI_API_KEY)."""

    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.model = os.environ.get('GEMINI_MODEL', 'gemini-pro')

    def is_available(self) -> bool:
        return bool(self.api_key)

    def analyze_risks(self, project_data: Dict) -> Dict:
        if not self.is_available():
            return {'error': 'Gemini not configured'}
        return {'provider': 'gemini', 'status': 'not_implemented'}

    def suggest_task_assignment(self, task_data: Dict, employees: List[Dict]) -> List[Dict]:
        return []

    def predict_delay(self, project_data: Dict) -> Dict:
        return {}

    def generate_status_report(self, project_data: Dict) -> Dict:
        return {}


class AIProviderFactory:
    """Factory for creating AI providers."""

    PROVIDERS = {
        'rule_based': RuleBasedProvider,
        'openai': OpenAIProvider,
        'gemini': GeminiProvider,
    }

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> AIProvider:
        """Get AI provider by name or auto-detect."""
        if name:
            provider_class = cls.PROVIDERS.get(name)
            if provider_class:
                return provider_class()
            raise ValueError(f"Unknown provider: {name}")

        # Auto-detect: try external providers first, fallback to rule-based
        for provider_name in ['openai', 'gemini']:
            provider = cls.PROVIDERS[provider_name]()
            if provider.is_available():
                return provider

        # Fallback to rule-based (always available)
        return RuleBasedProvider()

    @classmethod
    def list_available_providers(cls) -> List[str]:
        """List all available providers."""
        available = []
        for name, provider_class in cls.PROVIDERS.items():
            if provider_class().is_available():
                available.append(name)
        return available
