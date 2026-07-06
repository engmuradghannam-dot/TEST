from apps.core.ai_adapter import AIProviderFactory

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Project, Task, RiskRegister, IssueLog, TimeEntry
from apps.hr.models import Employee


class ProjectAIAssistantViewSet(viewsets.ViewSet):
    """AI-powered project management assistant.

    Provides intelligent analysis and recommendations for projects
    without requiring external AI APIs - uses rule-based intelligence
    combined with statistical analysis.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def analyze_risks(self, request):
        """Analyze project risks and provide mitigation recommendations."""
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        risks = project.risks.all()
        issues = project.issues.all()
        tasks = project.tasks.all()

        # Risk analysis
        high_risks = risks.filter(probability__gte=4, impact__gte=4)
        medium_risks = risks.filter(
            Q(probability__gte=3, impact__gte=3) | Q(probability__gte=4) | Q(impact__gte=4)
        ).exclude(pk__in=high_risks)

        # Pattern detection
        recommendations = []

        # Check for overdue milestones
        overdue_milestones = project.milestones.filter(
            status='Pending',
            due_date__lt=timezone.now().date()
        )
        if overdue_milestones.exists():
            recommendations.append({
                'type': 'schedule',
                'severity': 'high',
                'message': f'Found {overdue_milestones.count()} overdue milestone(s). Consider revising the project timeline.',
                'action': 'Review and update milestone dates or allocate more resources.'
            })

        # Check task completion rate
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='Completed').count()
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
            if completion_rate < 30 and project.progress_percent > 50:
                recommendations.append({
                    'type': 'progress',
                    'severity': 'medium',
                    'message': 'Project progress percentage seems inflated compared to actual task completion.',
                    'action': 'Verify progress tracking methodology.'
                })

        # Check resource allocation
        overloaded_employees = []
        for emp in Employee.objects.filter(tasks__project=project).distinct():
            active_tasks = emp.tasks.filter(project=project, status__in=['Open', 'Working']).count()
            if active_tasks > 5:
                overloaded_employees.append({
                    'name': str(emp),
                    'active_tasks': active_tasks
                })
        if overloaded_employees:
            recommendations.append({
                'type': 'resources',
                'severity': 'medium',
                'message': f'{len(overloaded_employees)} employee(s) have more than 5 active tasks.',
                'action': 'Redistribute tasks or hire additional resources.',
                'affected': overloaded_employees
            })

        # Budget analysis
        if project.actual_cost > project.budget * 0.8:
            recommendations.append({
                'type': 'budget',
                'severity': 'high' if project.actual_cost > project.budget else 'medium',
                'message': f'Project has used {(project.actual_cost/project.budget)*100:.1f}% of budget.',
                'action': 'Review cost controls and consider change requests for additional budget.'
            })

        # Time tracking analysis
        total_hours = sum((te.duration_hours for te in project.time_entries.all()), 0)
        if total_hours > 0:
            estimated_hours = project.estimated_cost / 100  # rough estimate
            if total_hours > estimated_hours * 1.5:
                recommendations.append({
                    'type': 'time',
                    'severity': 'medium',
                    'message': f'Actual hours ({total_hours:.1f}h) significantly exceed estimates.',
                    'action': 'Review task estimates and scope.'
                })

        return Response({
            'project': project.project_name,
            'risk_summary': {
                'total_risks': risks.count(),
                'high_risks': high_risks.count(),
                'medium_risks': medium_rarks.count(),
                'open_issues': issues.filter(status__in=['Open', 'In Progress']).count(),
            },
            'recommendations': recommendations,
            'health_score': self._calculate_health_score(project, risks, issues, tasks)
        })

    def _calculate_health_score(self, project, risks, issues, tasks):
        """Calculate an overall project health score (0-100)."""
        score = 100

        # Deduct for high risks
        score -= risks.filter(probability__gte=4, impact__gte=4).count() * 10

        # Deduct for overdue items
        overdue_tasks = tasks.filter(expected_end__lt=timezone.now().date(), status__in=['Open', 'Working'])
        score -= min(overdue_tasks.count() * 5, 30)

        # Deduct for budget overrun
        if project.budget > 0:
            budget_used = (project.actual_cost / project.budget) * 100
            if budget_used > 100:
                score -= 20
            elif budget_used > 80:
                score -= 10

        # Deduct for open issues
        open_issues = issues.filter(status__in=['Open', 'In Progress']).count()
        score -= min(open_issues * 3, 15)

        return max(0, min(100, score))

    @action(detail=False, methods=['post'])
    def suggest_task_assignment(self, request):
        """Suggest optimal task assignments based on skills and workload."""
        task_id = request.data.get('task_id')
        if not task_id:
            return Response({'error': 'task_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        project = task.project

        # Get employees in the same company with their workload
        suggestions = []
        for emp in Employee.objects.filter(company=project.company).distinct():
            active_tasks = emp.tasks.filter(status__in=['Open', 'Working']).count()
            completed_project_tasks = emp.tasks.filter(project=project, status='Completed').count()

            # Calculate suitability score
            score = 100
            score -= active_tasks * 10  # Penalty for high workload
            score += completed_project_tasks * 5  # Bonus for project familiarity

            # Check if employee is in the same department as task requirements
            if task.team and emp in task.team.members.all():
                score += 15

            suggestions.append({
                'employee_id': emp.id,
                'name': str(emp),
                'active_tasks': active_tasks,
                'completed_in_project': completed_project_tasks,
                'suitability_score': max(0, score),
                'reason': f'{"Same team" if task.team and emp in task.team.members.all() else ""} {"Low workload" if active_tasks < 3 else ""}'.strip()
            })

        suggestions.sort(key=lambda x: x['suitability_score'], reverse=True)

        return Response({
            'task': task.subject,
            'top_suggestions': suggestions[:5],
            'current_assignee': str(task.assigned_to) if task.assigned_to else None
        })

    @action(detail=False, methods=['post'])
    def predict_delay(self, request):
        """Predict if a project will be delayed based on current velocity."""
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks = project.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='Completed').count()

        if total_tasks == 0:
            return Response({'error': 'No tasks to analyze'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate velocity (tasks completed per day)
        days_since_start = (timezone.now().date() - (project.expected_start or timezone.now().date())).days or 1
        velocity = completed_tasks / max(days_since_start, 1)

        remaining_tasks = total_tasks - completed_tasks
        days_needed = remaining_tasks / max(velocity, 0.1)

        predicted_end = timezone.now().date() + timedelta(days=int(days_needed))
        expected_end = project.expected_end

        delay_days = 0
        if expected_end and predicted_end > expected_end:
            delay_days = (predicted_end - expected_end).days

        return Response({
            'project': project.project_name,
            'velocity': round(velocity, 2),
            'tasks_completed': completed_tasks,
            'tasks_remaining': remaining_tasks,
            'predicted_end': predicted_end.isoformat(),
            'expected_end': expected_end.isoformat() if expected_end else None,
            'delay_days': delay_days,
            'on_track': delay_days == 0,
            'risk_level': 'high' if delay_days > 14 else 'medium' if delay_days > 7 else 'low'
        })

    @action(detail=False, methods=['post'])
    def generate_status_report(self, request):
        """Generate an AI-powered project status report."""
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks = project.tasks.all()
        risks = project.risks.all()
        issues = project.issues.all()
        milestones = project.milestones.all()

        # Generate insights
        insights = []

        # Progress insight
        completion_rate = (tasks.filter(status='Completed').count() / max(tasks.count(), 1)) * 100
        insights.append(f"Project is {completion_rate:.0f}% complete with {tasks.filter(status='Working').count()} tasks in progress.")

        # Milestone insight
        upcoming_milestones = milestones.filter(status='Pending', due_date__gte=timezone.now().date()).order_by('due_date')[:3]
        if upcoming_milestones:
            insights.append(f"Upcoming milestones: {', '.join([m.name for m in upcoming_milestones])}.")

        # Risk insight
        critical_risks = risks.filter(probability__gte=4, impact__gte=4)
        if critical_risks:
            insights.append(f"⚠️ {critical_risks.count()} critical risks require immediate attention.")

        # Issue insight
        open_issues = issues.filter(status__in=['Open', 'In Progress'])
        if open_issues:
            high_severity = open_issues.filter(severity__in=['High', 'Critical'])
            insights.append(f"{open_issues.count()} open issues ({high_severity.count()} high severity).")

        # Budget insight
        if project.budget > 0:
            budget_pct = (project.actual_cost / project.budget) * 100
            insights.append(f"Budget utilization: {budget_pct:.1f}% ({project.actual_cost:,.0f} / {project.budget:,.0f} SAR).")

        return Response({
            'project': project.project_name,
            'generated_at': timezone.now().isoformat(),
            'executive_summary': f"""
Project {project.project_name} is currently {project.status.lower()}.
Overall progress: {project.progress_percent}%.
Health Score: {self._calculate_health_score(project, risks, issues, tasks)}/100.
            """.strip(),
            'insights': insights,
            'key_metrics': {
                'total_tasks': tasks.count(),
                'completed': tasks.filter(status='Completed').count(),
                'in_progress': tasks.filter(status='Working').count(),
                'overdue': tasks.filter(expected_end__lt=timezone.now().date(), status__in=['Open', 'Working']).count(),
                'open_risks': risks.filter(status='Open').count(),
                'open_issues': open_issues.count(),
                'budget_used_pct': round((project.actual_cost / project.budget) * 100, 1) if project.budget else 0,
            },
            'recommendations': self._generate_recommendations(project, tasks, risks, issues)
        })

    def _generate_recommendations(self, project, tasks, risks, issues):
        """Generate actionable recommendations."""
        recs = []

        # Check for stalled tasks
        stalled = tasks.filter(status='Working', expected_end__lt=timezone.now().date() - timedelta(days=7))
        if stalled:
            recs.append(f"Review {stalled.count()} stalled tasks that have been 'In Progress' for over a week.")

        # Check risk mitigation
        unmitigated = risks.filter(status='Open', probability__gte=3)
        if unmitigated:
            recs.append(f"Develop mitigation plans for {unmitigated.count()} high-probability risks.")

        # Check issue resolution time
        old_issues = issues.filter(status='Open', raised_date__lt=timezone.now().date() - timedelta(days=14))
        if old_issues:
            recs.append(f"Escalate {old_issues.count()} issues that have been open for over 2 weeks.")

        # Budget check
        if project.budget > 0 and project.actual_cost > project.budget * 0.9:
            recs.append("Prepare change request for potential budget overrun.")

        return recs
