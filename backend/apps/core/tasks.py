"""
Celery Tasks for CE-ERP OS
Async execution: workflows, AI processing, plugins, metrics, self-improvement
"""
import json
import logging
from datetime import datetime, timedelta
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction
from django.utils import timezone

from apps.core.event_bus import event_bus, DomainEvent, EventTypes, EventPriority
from apps.workflow.engine import (
    WorkflowDefinition, ProcessInstance, TaskInstance, ProcessStatus, TaskStatus,
    workflow_engine
)
from apps.core.state_machine import StateMachineInstance, StateMachineRegistry, StateMachineExecutor
from apps.core.ai_brain import llm_core, rag_memory, AIConversation
from apps.core.agent_layer import AgentTask, AgentAction, agent_orchestrator
from apps.core.self_improvement import (
    monitoring_layer, ai_analyzer, suggestion_engine, controlled_deployment,
    SystemImprovement, PerformanceMetric, ImprovementType
)
from apps.core.observability import metrics_collector, alert_manager, BusinessMetrics
from apps.plugins.enhanced_system import PluginRegistry, TenantPlugin, plugin_lifecycle_manager

logger = logging.getLogger(__name__)


# ============================================================
# Workflow Tasks
# ============================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def execute_workflow_task(self, process_id: str):
    """Execute a workflow process asynchronously"""
    try:
        instance = ProcessInstance.objects.get(id=process_id)
        if instance.status != ProcessStatus.RUNNING.value:
            logger.info(f"Process {process_id} is not running, skipping")
            return {'status': 'skipped', 'reason': instance.status}

        workflow_engine._execute_process(instance)

        return {
            'status': instance.status,
            'process_id': process_id,
            'completed_at': instance.completed_at.isoformat() if instance.completed_at else None
        }
    except Exception as exc:
        logger.error(f"Workflow execution failed: {exc}")
        try:
            self.retry(exc=exc)
        except MaxRetriesExceededError:
            instance = ProcessInstance.objects.get(id=process_id)
            workflow_engine._fail_process(instance, f"Max retries exceeded: {exc}")
            return {'status': 'failed', 'error': str(exc)}


@shared_task
def process_delayed_events():
    """Process events that have reached their delivery time"""
    event_bus.process_delayed_events()
    return {'status': 'processed'}


@shared_task
def cleanup_old_processes(days: int = 30):
    """Clean up completed/failed processes older than N days"""
    cutoff = timezone.now() - timedelta(days=days)
    old_processes = ProcessInstance.objects.filter(
        status__in=[ProcessStatus.COMPLETED.value, ProcessStatus.FAILED.value, ProcessStatus.CANCELLED.value],
        completed_at__lt=cutoff
    )
    count = old_processes.count()
    old_processes.delete()
    logger.info(f"Cleaned up {count} old processes")
    return {'deleted': count}


@shared_task
def check_overdue_tasks():
    """Check for overdue tasks and escalate"""
    overdue = TaskInstance.objects.filter(
        status__in=[TaskStatus.PENDING.value, TaskStatus.ACTIVE.value],
        due_date__lt=timezone.now()
    )

    for task in overdue:
        # Publish escalation event
        event = DomainEvent.create(
            event_type=EventTypes.WORKFLOW_APPROVAL_REQUIRED,
            aggregate_type="task",
            aggregate_id=str(task.id),
            tenant_id=task.process.tenant_id,
            payload={
                'task_name': task.node_name,
                'overdue_by_hours': (timezone.now() - task.due_date).total_seconds() / 3600
            },
            priority=EventPriority.HIGH
        )
        event_bus.publish(event)

    return {'escalated': overdue.count()}


# ============================================================
# AI Tasks
# ============================================================

@shared_task(bind=True, max_retries=2)
def execute_agent_task(self, task_data: dict):
    """Execute an AI agent task asynchronously"""
    try:
        from apps.core.agent_layer import AgentTask
        task = AgentTask(**task_data)
        result = agent_orchestrator.dispatch(task)
        return result
    except Exception as exc:
        logger.error(f"Agent task failed: {exc}")
        self.retry(exc=exc, countdown=30)


@shared_task
def generate_ai_embeddings():
    """Generate embeddings for knowledge base entries"""
    from apps.core.ai_brain import AIKnowledgeBase

    entries = AIKnowledgeBase.objects.filter(embedding_id='')
    for entry in entries:
        try:
            embedding = llm_core.embed(entry.content)
            doc_id = str(entry.id)
            rag_memory.add_document(
                collection='company_knowledge',
                doc_id=doc_id,
                text=entry.content,
                metadata={
                    'title': entry.title,
                    'category': entry.category,
                    'company_id': str(entry.company_id)
                },
                tenant_id=str(entry.company_id)
            )
            entry.embedding_id = doc_id
            entry.save()
        except Exception as e:
            logger.error(f"Failed to generate embedding for {entry.id}: {e}")

    return {'processed': entries.count()}


@shared_task
def ai_conversation_cleanup(days: int = 90):
    """Clean up old AI conversations"""
    cutoff = timezone.now() - timedelta(days=days)
    old_conversations = AIConversation.objects.filter(updated_at__lt=cutoff, is_active=False)
    count = old_conversations.count()
    old_conversations.delete()
    return {'deleted': count}


# ============================================================
# Self-Improvement Tasks
# ============================================================

@shared_task
def analyze_system_performance():
    """Periodic system performance analysis"""
    # Collect metrics
    from django.db import connection

    # Database query performance
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT query, calls, mean_exec_time 
            FROM pg_stat_statements 
            ORDER BY mean_exec_time DESC 
            LIMIT 10
        """)
        slow_queries = cursor.fetchall()

    # Record metrics
    for query, calls, mean_time in slow_queries:
        PerformanceMetric.objects.create(
            metric_name='slow_query',
            value=mean_time,
            unit='ms',
            tags={'query': query[:100], 'calls': calls}
        )

    # Analyze workflows
    workflow_data = []
    from apps.workflow.engine import ProcessInstance
    recent_processes = ProcessInstance.objects.filter(
        started_at__gte=timezone.now() - timedelta(days=7)
    )

    for p in recent_processes:
        duration = (p.completed_at - p.started_at).total_seconds() if p.completed_at else None
        workflow_data.append({
            'workflow': p.workflow.name,
            'status': p.status,
            'duration': duration,
            'tasks': p.tasks.count()
        })

    if workflow_data:
        analysis = ai_analyzer.analyze_workflows(workflow_data)

        # Generate improvement suggestions
        suggestion = suggestion_engine.generate_suggestion(
            analysis,
            ImprovementType.PERFORMANCE_TUNING
        )

        # Create improvement record
        SystemImprovement.objects.create(
            title=suggestion['suggestion'].get('title', 'Performance Analysis'),
            description=suggestion['suggestion'].get('description', ''),
            improvement_type=ImprovementType.PERFORMANCE_TUNING.value,
            status='detected',
            analysis_data=analysis,
            suggestion_data=suggestion
        )

    return {'analyzed': len(workflow_data)}


@shared_task
def check_and_alert():
    """Check metrics and fire alerts"""
    # Get current metrics
    from django.db.models import Avg, Count

    # Error rate
    recent_errors = PerformanceMetric.objects.filter(
        metric_name='error',
        recorded_at__gte=timezone.now() - timedelta(hours=1)
    ).count()

    # API latency
    avg_latency = PerformanceMetric.objects.filter(
        metric_name='api_latency',
        recorded_at__gte=timezone.now() - timedelta(hours=1)
    ).aggregate(avg=Avg('value'))['avg'] or 0

    metrics = {
        'system.errors': recent_errors,
        'system.api.latency': avg_latency
    }

    alerts = alert_manager.check_all(metrics)

    for alert in alerts:
        event = DomainEvent.create(
            event_type=EventTypes.ERROR_OCCURRED,
            aggregate_type="alert",
            aggregate_id=alert['rule'],
            tenant_id='',
            payload=alert,
            priority=EventPriority.HIGH
        )
        event_bus.publish(event)

    return {'alerts_fired': len(alerts)}


# ============================================================
# Plugin Tasks
# ============================================================

@shared_task
def plugin_install_task(tenant_plugin_id: str):
    """Async plugin installation"""
    try:
        tp = TenantPlugin.objects.get(id=tenant_plugin_id)
        result = plugin_lifecycle_manager.activate(tp)
        return result
    except Exception as e:
        logger.error(f"Plugin installation failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def plugin_update_task(tenant_plugin_id: str, new_plugin_id: str):
    """Async plugin update"""
    try:
        tp = TenantPlugin.objects.get(id=tenant_plugin_id)
        new_plugin = PluginRegistry.objects.get(id=new_plugin_id)
        result = plugin_lifecycle_manager.update(tp, new_plugin)
        return result
    except Exception as e:
        logger.error(f"Plugin update failed: {e}")
        return {'success': False, 'error': str(e)}


# ============================================================
# Business Metrics Tasks
# ============================================================

@shared_task
def collect_business_metrics():
    """Collect periodic business metrics"""
    from apps.accounts.models import Invoice
    from apps.buying.models import PurchaseOrder
    from apps.selling.models import SalesOrder
    from apps.hr.models import Employee

    # Invoice metrics
    today_invoices = Invoice.objects.filter(created_at__date=timezone.now().date())
    for inv in today_invoices:
        BusinessMetrics.record_invoice_created(
            amount=float(inv.total_amount),
            tenant_id=str(inv.company_id)
        )

    # Purchase order metrics
    today_pos = PurchaseOrder.objects.filter(created_at__date=timezone.now().date())
    for po in today_pos:
        BusinessMetrics.record_purchase_order_created(
            amount=float(po.total_amount),
            tenant_id=str(po.company_id)
        )

    # Sales order metrics
    today_sos = SalesOrder.objects.filter(created_at__date=timezone.now().date())
    for so in today_sos:
        BusinessMetrics.record_sales_order_created(
            amount=float(so.total_amount),
            tenant_id=str(so.company_id)
        )

    # Employee metrics
    new_employees = Employee.objects.filter(created_at__date=timezone.now().date())
    for emp in new_employees:
        BusinessMetrics.record_employee_hired(
            tenant_id=str(emp.company_id)
        )

    return {
        'invoices': today_invoices.count(),
        'purchase_orders': today_pos.count(),
        'sales_orders': today_sos.count(),
        'new_employees': new_employees.count()
    }


# ============================================================
# Maintenance Tasks
# ============================================================

@shared_task
def daily_maintenance():
    """Daily system maintenance"""
    results = {}

    # Cleanup old processes
    results['processes'] = cleanup_old_processes.delay(days=30).get()

    # Check overdue tasks
    results['overdue'] = check_overdue_tasks.delay().get()

    # Cleanup old conversations
    results['conversations'] = ai_conversation_cleanup.delay(days=90).get()

    # Collect business metrics
    results['metrics'] = collect_business_metrics.delay().get()

    # System analysis
    results['analysis'] = analyze_system_performance.delay().get()

    # Check alerts
    results['alerts'] = check_and_alert.delay().get()

    logger.info(f"Daily maintenance completed: {results}")
    return results
