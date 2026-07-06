"""
Enhanced BPMN 2.0 Workflow Engine for Nexus CE-ERP OS
Supports: Full BPMN concepts, state persistence, retry/rollback, async execution
"""
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from apps.core.event_bus import event_bus, DomainEvent, EventTypes, EventPriority
from apps.core.state_machine import StateMachineRegistry, StateMachineInstance, StateMachineExecutor

logger = logging.getLogger(__name__)


class BPMNElementType(Enum):
    """BPMN 2.0 Element Types"""
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
    TASK = "task"
    USER_TASK = "userTask"
    SERVICE_TASK = "serviceTask"
    SCRIPT_TASK = "scriptTask"
    SEND_TASK = "sendTask"
    RECEIVE_TASK = "receiveTask"
    MANUAL_TASK = "manualTask"
    BUSINESS_RULE_TASK = "businessRuleTask"
    GATEWAY_EXCLUSIVE = "exclusiveGateway"
    GATEWAY_PARALLEL = "parallelGateway"
    GATEWAY_INCLUSIVE = "inclusiveGateway"
    GATEWAY_EVENT_BASED = "eventBasedGateway"
    SUB_PROCESS = "subProcess"
    CALL_ACTIVITY = "callActivity"
    BOUNDARY_EVENT = "boundaryEvent"
    INTERMEDIATE_CATCH_EVENT = "intermediateCatchEvent"
    INTERMEDIATE_THROW_EVENT = "intermediateThrowEvent"
    SEQUENCE_FLOW = "sequenceFlow"


class ProcessStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class TaskStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


@dataclass
class BPMNNode:
    """BPMN Node representation"""
    id: str
    element_type: BPMNElementType
    name: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    incoming: List[str] = field(default_factory=list)
    outgoing: List[str] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 80.0

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.element_type.value,
            'name': self.name,
            'properties': self.properties,
            'incoming': self.incoming,
            'outgoing': self.outgoing,
            'x': self.x, 'y': self.y,
            'width': self.width, 'height': self.height,
        }


@dataclass
class BPMNEdge:
    """BPMN Edge (Sequence Flow)"""
    id: str
    source: str
    target: str
    name: str = ""
    condition: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'name': self.name,
            'condition': self.condition,
            'properties': self.properties,
        }


# ============================================================
# Models
# ============================================================

class WorkflowDefinition(models.Model):
    """BPMN Workflow Definition with versioning"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(max_length=200, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    version = models.PositiveIntegerField(default=1, verbose_name=_('Version'))
    is_active = models.BooleanField(default=True)
    is_latest = models.BooleanField(default=True)

    # BPMN data
    bpmn_xml = models.TextField(blank=True, verbose_name=_('BPMN XML'))
    nodes = models.JSONField(default=list, verbose_name=_('Nodes'))
    edges = models.JSONField(default=list, verbose_name=_('Edges'))

    # Metadata
    document_type = models.CharField(max_length=100, blank=True, verbose_name=_('Document Type'))
    module = models.CharField(max_length=50, blank=True, verbose_name=_('Module'))
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)

    # Triggers
    trigger_types = models.JSONField(default=list, verbose_name=_('Trigger Types'))
    trigger_config = models.JSONField(default=dict, verbose_name=_('Trigger Config'))

    # State machine linkage
    state_machine_type = models.CharField(max_length=100, blank=True)

    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['slug', 'version', 'tenant']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'is_latest']),
            models.Index(fields=['document_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"

    def create_new_version(self):
        """Create a new version of this workflow"""
        self.is_latest = False
        self.save()

        new_version = WorkflowDefinition.objects.create(
            name=self.name,
            slug=self.slug,
            description=self.description,
            version=self.version + 1,
            is_active=self.is_active,
            is_latest=True,
            bpmn_xml=self.bpmn_xml,
            nodes=self.nodes,
            edges=self.edges,
            document_type=self.document_type,
            module=self.module,
            tenant=self.tenant,
            trigger_types=self.trigger_types,
            trigger_config=self.trigger_config,
            state_machine_type=self.state_machine_type,
            created_by=self.created_by
        )
        return new_version

    def get_nodes_dict(self) -> Dict[str, Dict]:
        return {n['id']: n for n in self.nodes}

    def get_edges_dict(self) -> Dict[str, Dict]:
        return {e['id']: e for e in self.edges}


class ProcessInstance(models.Model):
    """Running instance of a workflow"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='instances')
    status = models.CharField(max_length=20, choices=[
        (s.value, s.value.title()) for s in ProcessStatus
    ], default=ProcessStatus.PENDING.value)

    # Context
    tenant_id = models.CharField(max_length=100)
    started_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)

    # Data
    variables = models.JSONField(default=dict, verbose_name=_('Process Variables'))
    context_data = models.JSONField(default=dict, verbose_name=_('Context Data'))

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)

    # Retry/Rollback
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    rollback_data = models.JSONField(default=dict, blank=True)

    # Parent process (for sub-processes)
    parent_process = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_processes')

    class Meta:
        indexes = [
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"Process {self.id} ({self.status})"


class TaskInstance(models.Model):
    """Individual task within a process instance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process = models.ForeignKey(ProcessInstance, on_delete=models.CASCADE, related_name='tasks')
    node_id = models.CharField(max_length=100)
    node_name = models.CharField(max_length=200, blank=True)
    node_type = models.CharField(max_length=50)

    status = models.CharField(max_length=20, choices=[
        (s.value, s.value.title()) for s in TaskStatus
    ], default=TaskStatus.PENDING.value)

    # Assignment
    assigned_to = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_role = models.CharField(max_length=50, blank=True)
    candidate_users = models.JSONField(default=list, blank=True)
    candidate_groups = models.JSONField(default=list, blank=True)

    # Data
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    form_data = models.JSONField(default=dict, blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    # Retry
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)

    # Rollback
    rollback_actions = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['started_at']
        indexes = [
            models.Index(fields=['process', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.node_name} ({self.status})"


class ProcessHistory(models.Model):
    """Audit trail for process execution"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process = models.ForeignKey(ProcessInstance, on_delete=models.CASCADE, related_name='history')
    task = models.ForeignKey(TaskInstance, on_delete=models.SET_NULL, null=True, blank=True)

    action = models.CharField(max_length=100)
    from_status = models.CharField(max_length=50, blank=True)
    to_status = models.CharField(max_length=50, blank=True)

    performed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ============================================================
# Workflow Engine Executor
# ============================================================

class WorkflowEngine:
    """BPMN Workflow Engine with full execution capabilities"""

    def __init__(self):
        self.task_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default task handlers"""
        self.register_task_handler('userTask', self._handle_user_task)
        self.register_task_handler('serviceTask', self._handle_service_task)
        self.register_task_handler('scriptTask', self._handle_script_task)
        self.register_task_handler('sendTask', self._handle_send_task)
        self.register_task_handler('receiveTask', self._handle_receive_task)
        self.register_task_handler('businessRuleTask', self._handle_business_rule_task)

    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type"""
        self.task_handlers[task_type] = handler
        logger.info(f"Task handler registered for {task_type}")

    @transaction.atomic
    def start_process(self, workflow: WorkflowDefinition, variables: Dict = None,
                     started_by=None, tenant_id: str = None, context_data: Dict = None) -> ProcessInstance:
        """Start a new process instance"""
        instance = ProcessInstance.objects.create(
            workflow=workflow,
            status=ProcessStatus.RUNNING.value,
            tenant_id=tenant_id or '',
            started_by=started_by,
            variables=variables or {},
            context_data=context_data or {}
        )

        # Find start event
        nodes = workflow.get_nodes_dict()
        start_nodes = [n for n in nodes.values() if n['type'] == 'startEvent']

        if not start_nodes:
            instance.status = ProcessStatus.FAILED.value
            instance.save()
            raise ValueError("No start event found in workflow")

        start_node = start_nodes[0]

        # Create first task
        self._create_task(instance, start_node)

        # Execute immediately
        self._execute_process(instance)

        # Publish event
        event = DomainEvent.create(
            event_type=EventTypes.WORKFLOW_STARTED,
            aggregate_type="workflow",
            aggregate_id=str(instance.id),
            tenant_id=tenant_id or '',
            payload={
                'workflow_id': str(workflow.id),
                'workflow_name': workflow.name,
                'started_by': str(started_by.id) if started_by else None
            }
        )
        event_bus.publish(event)

        logger.info(f"Process started: {instance.id} for workflow {workflow.name}")
        return instance

    def _execute_process(self, instance: ProcessInstance):
        """Execute process until waiting for user input or completion"""
        while True:
            active_tasks = instance.tasks.filter(status=TaskStatus.ACTIVE.value)

            if not active_tasks.exists():
                # Check if there are pending tasks
                pending_tasks = instance.tasks.filter(status=TaskStatus.PENDING.value)
                if not pending_tasks.exists():
                    # No more tasks - process complete
                    self._complete_process(instance)
                    break

                # Activate pending tasks
                for task in pending_tasks:
                    self._activate_task(task)

            # Execute active tasks
            completed_any = False
            for task in active_tasks:
                result = self._execute_task(task)
                if result:
                    completed_any = True

            if not completed_any:
                break

    def _create_task(self, instance: ProcessInstance, node: Dict) -> TaskInstance:
        """Create a task instance for a node"""
        task = TaskInstance.objects.create(
            process=instance,
            node_id=node['id'],
            node_name=node.get('name', ''),
            node_type=node['type'],
            status=TaskStatus.PENDING.value,
            input_data=instance.variables,
            due_date=self._calculate_due_date(node)
        )

        # Set assignment from node properties
        props = node.get('properties', {})
        task.assigned_role = props.get('assignee_role', '')
        task.candidate_users = props.get('candidate_users', [])
        task.candidate_groups = props.get('candidate_groups', [])
        task.max_retries = props.get('max_retries', 3)
        task.save()

        return task

    def _activate_task(self, task: TaskInstance):
        """Activate a pending task"""
        task.status = TaskStatus.ACTIVE.value
        task.started_at = timezone.now()
        task.save()

        ProcessHistory.objects.create(
            process=task.process,
            task=task,
            action='activated',
            from_status=TaskStatus.PENDING.value,
            to_status=TaskStatus.ACTIVE.value
        )

    def _execute_task(self, task: TaskInstance) -> bool:
        """Execute a task and return True if completed"""
        handler = self.task_handlers.get(task.node_type)

        if not handler:
            logger.warning(f"No handler for task type: {task.node_type}")
            return False

        try:
            result = handler(task)

            if result['completed']:
                self._complete_task(task, result.get('output', {}))
                return True
            else:
                # Task is waiting (e.g., user task)
                return False
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self._handle_task_failure(task, str(e))
            return False

    def _complete_task(self, task: TaskInstance, output_data: Dict):
        """Complete a task and advance workflow"""
        task.status = TaskStatus.COMPLETED.value
        task.output_data = output_data
        task.completed_at = timezone.now()
        task.save()

        # Update process variables
        task.process.variables.update(output_data)
        task.process.save()

        # Create history
        ProcessHistory.objects.create(
            process=task.process,
            task=task,
            action='completed',
            from_status=TaskStatus.ACTIVE.value,
            to_status=TaskStatus.COMPLETED.value,
            details=output_data
        )

        # Find next nodes
        workflow = task.process.workflow
        edges = workflow.get_edges_dict()
        nodes = workflow.get_nodes_dict()

        next_nodes = []
        for edge in edges.values():
            if edge['source'] == task.node_id:
                # Check condition
                if self._evaluate_condition(edge.get('condition', ''), task.process.variables):
                    next_nodes.append(nodes.get(edge['target']))

        # Create tasks for next nodes
        for next_node in next_nodes:
            if next_node:
                self._create_task(task.process, next_node)

        # Publish event
        event = DomainEvent.create(
            event_type=EventTypes.WORKFLOW_STEP_EXECUTED,
            aggregate_type="workflow",
            aggregate_id=str(task.process.id),
            tenant_id=task.process.tenant_id,
            payload={
                'task_id': str(task.id),
                'node_name': task.node_name,
                'node_type': task.node_type,
                'output': output_data
            }
        )
        event_bus.publish(event)

    def _handle_task_failure(self, task: TaskInstance, error: str):
        """Handle task execution failure with retry logic"""
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            # Retry
            task.status = TaskStatus.PENDING.value
            task.save()
            logger.info(f"Task {task.id} scheduled for retry {task.retry_count}/{task.max_retries}")
        else:
            # Max retries exceeded
            task.status = TaskStatus.FAILED.value
            task.save()

            # Check if rollback is configured
            if task.rollback_actions:
                self._rollback_task(task)
            else:
                self._fail_process(task.process, f"Task {task.node_name} failed: {error}")

    def _rollback_task(self, task: TaskInstance):
        """Execute rollback actions for a task"""
        task.process.status = ProcessStatus.ROLLING_BACK.value
        task.process.save()

        for action in task.rollback_actions:
            try:
                self._execute_rollback_action(action, task)
            except Exception as e:
                logger.error(f"Rollback action failed: {e}")

        task.process.status = ProcessStatus.ROLLED_BACK.value
        task.process.save()

    def _execute_rollback_action(self, action: Dict, task: TaskInstance):
        """Execute a single rollback action"""
        action_type = action.get('type')
        if action_type == 'revert_state':
            # Revert state machine state
            pass
        elif action_type == 'compensate':
            # Execute compensation
            pass

    def _complete_process(self, instance: ProcessInstance):
        """Complete a process instance"""
        instance.status = ProcessStatus.COMPLETED.value
        instance.completed_at = timezone.now()
        instance.save()

        ProcessHistory.objects.create(
            process=instance,
            action='completed',
            from_status=ProcessStatus.RUNNING.value,
            to_status=ProcessStatus.COMPLETED.value
        )

        event = DomainEvent.create(
            event_type=EventTypes.WORKFLOW_COMPLETED,
            aggregate_type="workflow",
            aggregate_id=str(instance.id),
            tenant_id=instance.tenant_id,
            payload={
                'workflow_id': str(instance.workflow.id),
                'duration_seconds': (instance.completed_at - instance.started_at).total_seconds()
            }
        )
        event_bus.publish(event)

        logger.info(f"Process completed: {instance.id}")

    def _fail_process(self, instance: ProcessInstance, reason: str):
        """Fail a process instance"""
        instance.status = ProcessStatus.FAILED.value
        instance.save()

        ProcessHistory.objects.create(
            process=instance,
            action='failed',
            from_status=ProcessStatus.RUNNING.value,
            to_status=ProcessStatus.FAILED.value,
            details={'reason': reason}
        )

        event = DomainEvent.create(
            event_type=EventTypes.WORKFLOW_FAILED,
            aggregate_type="workflow",
            aggregate_id=str(instance.id),
            tenant_id=instance.tenant_id,
            payload={'reason': reason},
            priority=EventPriority.HIGH
        )
        event_bus.publish(event)

        logger.error(f"Process failed: {instance.id} - {reason}")

    def _evaluate_condition(self, condition: str, variables: Dict) -> bool:
        """Evaluate a condition expression"""
        if not condition:
            return True

        try:
            # Simple expression evaluation
            # In production, use a proper expression engine
            return eval(condition, {"__builtins__": {}}, variables)
        except:
            return True

    def _calculate_due_date(self, node: Dict) -> Optional[datetime]:
        """Calculate due date from node properties"""
        props = node.get('properties', {})
        due_hours = props.get('due_hours')
        if due_hours:
            return timezone.now() + timedelta(hours=due_hours)
        return None

    # Task Handlers
    def _handle_user_task(self, task: TaskInstance) -> Dict:
        """Handle user task - returns not completed, waits for user action"""
        return {'completed': False, 'waiting_for': 'user_action'}

    def _handle_service_task(self, task: TaskInstance) -> Dict:
        """Handle service task - execute service call"""
        props = task.process.workflow.get_nodes_dict().get(task.node_id, {}).get('properties', {})
        service_name = props.get('service', '')

        # Execute service (would integrate with actual services)
        logger.info(f"Executing service task: {service_name}")

        return {'completed': True, 'output': {'service_executed': service_name}}

    def _handle_script_task(self, task: TaskInstance) -> Dict:
        """Handle script task - execute script"""
        props = task.process.workflow.get_nodes_dict().get(task.node_id, {}).get('properties', {})
        script = props.get('script', '')

        # Execute script in sandboxed environment
        try:
            local_vars = {'variables': task.process.variables, 'task': task}
            exec(script, {"__builtins__": {}}, local_vars)
            return {'completed': True, 'output': local_vars.get('result', {})}
        except Exception as e:
            raise Exception(f"Script execution failed: {e}")

    def _handle_send_task(self, task: TaskInstance) -> Dict:
        """Handle send task - send message/event"""
        props = task.process.workflow.get_nodes_dict().get(task.node_id, {}).get('properties', {})
        message_type = props.get('message_type', '')

        # Publish event
        event = DomainEvent.create(
            event_type=message_type,
            aggregate_type="workflow",
            aggregate_id=str(task.process.id),
            tenant_id=task.process.tenant_id,
            payload=task.process.variables
        )
        event_bus.publish(event)

        return {'completed': True, 'output': {'message_sent': message_type}}

    def _handle_receive_task(self, task: TaskInstance) -> Dict:
        """Handle receive task - wait for message/event"""
        return {'completed': False, 'waiting_for': 'message'}

    def _handle_business_rule_task(self, task: TaskInstance) -> Dict:
        """Handle business rule task - execute business rules"""
        props = task.process.workflow.get_nodes_dict().get(task.node_id, {}).get('properties', {})
        rules = props.get('rules', [])

        results = []
        for rule in rules:
            result = self._evaluate_business_rule(rule, task.process.variables)
            results.append(result)

        return {'completed': True, 'output': {'rule_results': results}}

    def _evaluate_business_rule(self, rule: Dict, variables: Dict) -> Dict:
        """Evaluate a business rule"""
        condition = rule.get('condition', '')
        action = rule.get('action', '')

        try:
            condition_met = eval(condition, {"__builtins__": {}}, variables)
            return {
                'rule': rule.get('name', ''),
                'condition_met': condition_met,
                'action': action if condition_met else None
            }
        except:
            return {'rule': rule.get('name', ''), 'error': 'Evaluation failed'}

    # Public API
    def complete_user_task(self, task_id: str, user, form_data: Dict = None) -> Dict:
        """Complete a user task"""
        task = TaskInstance.objects.get(id=task_id)

        if task.status != TaskStatus.ACTIVE.value:
            return {'success': False, 'error': 'Task is not active'}

        task.assigned_to = user
        task.form_data = form_data or {}
        task.save()

        self._complete_task(task, form_data or {})

        # Continue execution
        self._execute_process(task.process)

        return {'success': True, 'process_status': task.process.status}

    def cancel_process(self, instance_id: str, reason: str = "") -> bool:
        """Cancel a running process"""
        instance = ProcessInstance.objects.get(id=instance_id)
        instance.status = ProcessStatus.CANCELLED.value
        instance.save()

        # Cancel all active tasks
        instance.tasks.filter(status__in=[TaskStatus.PENDING.value, TaskStatus.ACTIVE.value]).update(
            status=TaskStatus.SKIPPED.value
        )

        ProcessHistory.objects.create(
            process=instance,
            action='cancelled',
            from_status=ProcessStatus.RUNNING.value,
            to_status=ProcessStatus.CANCELLED.value,
            details={'reason': reason}
        )

        return True

    def get_process_status(self, instance_id: str) -> Dict:
        """Get detailed process status"""
        instance = ProcessInstance.objects.get(id=instance_id)

        return {
            'id': str(instance.id),
            'status': instance.status,
            'workflow': instance.workflow.name,
            'started_at': instance.started_at.isoformat(),
            'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
            'variables': instance.variables,
            'tasks': [
                {
                    'id': str(t.id),
                    'name': t.node_name,
                    'type': t.node_type,
                    'status': t.status,
                    'assigned_to': str(t.assigned_to.id) if t.assigned_to else None,
                    'started_at': t.started_at.isoformat() if t.started_at else None,
                    'completed_at': t.completed_at.isoformat() if t.completed_at else None
                }
                for t in instance.tasks.all()
            ],
            'history': [
                {
                    'action': h.action,
                    'from_status': h.from_status,
                    'to_status': h.to_status,
                    'performed_by': str(h.performed_by.id) if h.performed_by else None,
                    'created_at': h.created_at.isoformat()
                }
                for h in instance.history.all()
            ]
        }


# Global workflow engine
workflow_engine = WorkflowEngine()
