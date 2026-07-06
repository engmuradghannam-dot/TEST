"""
BPMN 2.0 Workflow Engine for Nexus SaaS
Real state machine with visual designer support
"""
import uuid
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import JSONField
import logging

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
    POOL = "pool"
    LANE = "lane"
    DATA_OBJECT = "dataObject"
    DATA_STORE = "dataStore"
    SEQUENCE_FLOW = "sequenceFlow"
    MESSAGE_FLOW = "messageFlow"
    ASSOCIATION = "association"
    BOUNDARY_EVENT = "boundaryEvent"
    INTERMEDIATE_CATCH_EVENT = "intermediateCatchEvent"
    INTERMEDIATE_THROW_EVENT = "intermediateThrowEvent"


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


class WorkflowDefinition(models.Model):
    """BPMN Workflow Definition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    version = models.PositiveIntegerField(default=1, verbose_name=_('Version'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))

    # BPMN XML or JSON
    bpmn_xml = models.TextField(blank=True, verbose_name=_('BPMN XML'))
    bpmn_json = models.JSONField(default=dict, verbose_name=_('BPMN JSON'))

    # Parsed structure
    nodes = models.JSONField(default=list, verbose_name=_('Nodes'))
    edges = models.JSONField(default=list, verbose_name=_('Edges'))

    # Metadata
    category = models.CharField(max_length=100, blank=True, verbose_name=_('Category'))
    tags = models.JSONField(default=list, blank=True, verbose_name=_('Tags'))
    icon = models.URLField(blank=True, verbose_name=_('Icon'))

    # Permissions
    allowed_groups = models.JSONField(default=list, blank=True, verbose_name=_('Allowed Groups'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('tenants.TenantUser', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Workflow Definition')
        verbose_name_plural = _('Workflow Definitions')
        unique_together = ['slug', 'version']

    def __str__(self):
        return f"{self.name} v{self.version}"

    def parse_bpmn(self):
        """Parse BPMN JSON into nodes and edges"""
        if not self.bpmn_json:
            return

        data = self.bpmn_json
        self.nodes = []
        self.edges = []

        for node_data in data.get('nodes', []):
            node = BPMNNode(
                id=node_data['id'],
                element_type=BPMNElementType(node_data['type']),
                name=node_data.get('name', ''),
                properties=node_data.get('properties', {}),
                incoming=node_data.get('incoming', []),
                outgoing=node_data.get('outgoing', []),
                x=node_data.get('x', 0),
                y=node_data.get('y', 0),
                width=node_data.get('width', 100),
                height=node_data.get('height', 80),
            )
            self.nodes.append(node.to_dict())

        for edge_data in data.get('edges', []):
            edge = BPMNEdge(
                id=edge_data['id'],
                source=edge_data['source'],
                target=edge_data['target'],
                name=edge_data.get('name', ''),
                condition=edge_data.get('condition', ''),
                properties=edge_data.get('properties', {}),
            )
            self.edges.append(edge.to_dict())

        self.save(update_fields=['nodes', 'edges'])

    def get_start_nodes(self):
        """Get all start events"""
        return [n for n in self.nodes if n['type'] == BPMNElementType.START_EVENT.value]

    def get_node(self, node_id):
        """Get node by ID"""
        for node in self.nodes:
            if node['id'] == node_id:
                return node
        return None

    def get_outgoing_edges(self, node_id):
        """Get outgoing edges from a node"""
        return [e for e in self.edges if e['source'] == node_id]


class WorkflowInstance(models.Model):
    """Running Workflow Instance (Process Instance)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='instances')

    # State Machine
    class Status(models.TextChoices):
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        SUSPENDED = 'suspended', _('Suspended')
        TERMINATED = 'terminated', _('Terminated')
        ERROR = 'error', _('Error')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)

    # Current state
    current_nodes = models.JSONField(default=list, verbose_name=_('Current Active Nodes'))
    completed_nodes = models.JSONField(default=list, verbose_name=_('Completed Nodes'))

    # Context/Data
    variables = models.JSONField(default=dict, verbose_name=_('Process Variables'))

    # Business context
    entity_type = models.CharField(max_length=100, blank=True, verbose_name=_('Entity Type'))
    entity_id = models.CharField(max_length=100, blank=True, verbose_name=_('Entity ID'))

    # Audit
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey('tenants.TenantUser', on_delete=models.SET_NULL, null=True, related_name='started_workflows')

    class Meta:
        ordering = ['-started_at']
        verbose_name = _('Workflow Instance')
        verbose_name_plural = _('Workflow Instances')

    def __str__(self):
        return f"{self.definition.name} #{self.id} ({self.status})"


class WorkflowTask(models.Model):
    """User Task in Workflow"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='tasks')
    node_id = models.CharField(max_length=100, verbose_name=_('Node ID'))
    node_name = models.CharField(max_length=200, verbose_name=_('Node Name'))

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ASSIGNED = 'assigned', _('Assigned')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        DELEGATED = 'delegated', _('Delegated')
        ESCALATED = 'escalated', _('Escalated')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    assignee = models.ForeignKey('tenants.TenantUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    candidate_groups = models.JSONField(default=list, blank=True, verbose_name=_('Candidate Groups'))
    candidate_users = models.JSONField(default=list, blank=True, verbose_name=_('Candidate Users'))

    # Form data
    form_schema = models.JSONField(default=dict, blank=True, verbose_name=_('Form Schema'))
    form_data = models.JSONField(default=dict, blank=True, verbose_name=_('Form Data'))

    # Due date & priority
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveIntegerField(default=5, verbose_name=_('Priority'))  # 1-10

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = _('Workflow Task')
        verbose_name_plural = _('Workflow Tasks')

    def __str__(self):
        return f"{self.node_name} ({self.status})"


class WorkflowEngine:
    """
    Real BPMN Workflow Engine
    Executes workflow instances with state machine logic
    """

    def __init__(self):
        self.task_handlers: Dict[str, Callable] = {}
        self.gateway_evaluators: Dict[str, Callable] = {}

    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a handler for a specific task type"""
        self.task_handlers[task_type] = handler

    def register_gateway_evaluator(self, gateway_type: str, evaluator: Callable):
        """Register a condition evaluator for gateways"""
        self.gateway_evaluators[gateway_type] = evaluator

    def start_instance(self, definition: WorkflowDefinition, variables: Dict = None, 
                       user=None, entity_type: str = '', entity_id: str = '') -> WorkflowInstance:
        """Start a new workflow instance"""
        instance = WorkflowInstance.objects.create(
            definition=definition,
            variables=variables or {},
            entity_type=entity_type,
            entity_id=entity_id,
            started_by=user,
            status=WorkflowInstance.Status.RUNNING,
        )

        # Activate start nodes
        start_nodes = definition.get_start_nodes()
        instance.current_nodes = [n['id'] for n in start_nodes]
        instance.save()

        # Process start nodes
        for node in start_nodes:
            self._process_node(instance, node['id'])

        logger.info(f"Workflow instance {instance.id} started")
        return instance

    def _process_node(self, instance: WorkflowInstance, node_id: str):
        """Process a single node"""
        definition = instance.definition
        node = definition.get_node(node_id)

        if not node:
            logger.error(f"Node {node_id} not found in definition")
            return

        node_type = node['type']

        # Handle different node types
        if node_type == BPMNElementType.START_EVENT.value:
            self._handle_start_event(instance, node)

        elif node_type == BPMNElementType.END_EVENT.value:
            self._handle_end_event(instance, node)

        elif node_type in [BPMNElementType.TASK.value, BPMNElementType.USER_TASK.value]:
            self._handle_task(instance, node)

        elif node_type == BPMNElementType.SERVICE_TASK.value:
            self._handle_service_task(instance, node)

        elif node_type == BPMNElementType.SCRIPT_TASK.value:
            self._handle_script_task(instance, node)

        elif node_type == BPMNElementType.GATEWAY_EXCLUSIVE.value:
            self._handle_exclusive_gateway(instance, node)

        elif node_type == BPMNElementType.GATEWAY_PARALLEL.value:
            self._handle_parallel_gateway(instance, node)

        elif node_type == BPMNElementType.SUB_PROCESS.value:
            self._handle_sub_process(instance, node)

        else:
            logger.warning(f"Unknown node type: {node_type}")

    def _handle_start_event(self, instance: WorkflowInstance, node: dict):
        """Handle start event - just move to next node"""
        self._complete_node(instance, node['id'])
        self._move_to_next(instance, node['id'])

    def _handle_end_event(self, instance: WorkflowInstance, node: dict):
        """Handle end event - complete workflow"""
        self._complete_node(instance, node['id'])

        # Check if all paths completed
        if not instance.current_nodes:
            instance.status = WorkflowInstance.Status.COMPLETED
            from django.utils import timezone
            instance.completed_at = timezone.now()
            instance.save()
            logger.info(f"Workflow instance {instance.id} completed")

    def _handle_task(self, instance: WorkflowInstance, node: dict):
        """Handle user task - create task for user"""
        properties = node.get('properties', {})

        # Create workflow task
        task = WorkflowTask.objects.create(
            instance=instance,
            node_id=node['id'],
            node_name=node.get('name', 'Task'),
            form_schema=properties.get('formSchema', {}),
            candidate_groups=properties.get('candidateGroups', []),
            candidate_users=properties.get('candidateUsers', []),
            priority=properties.get('priority', 5),
        )

        logger.info(f"Task created: {task.id} for node {node['id']}")

    def _handle_service_task(self, instance: WorkflowInstance, node: dict):
        """Handle service task - execute automatically"""
        properties = node.get('properties', {})
        service_type = properties.get('serviceType', '')

        # Execute registered handler
        handler = self.task_handlers.get(service_type)
        if handler:
            try:
                result = handler(instance, node, instance.variables)
                instance.variables[f"{node['id']}_result"] = result
                instance.save()
                self._complete_node(instance, node['id'])
                self._move_to_next(instance, node['id'])
            except Exception as e:
                logger.error(f"Service task failed: {e}")
                instance.status = WorkflowInstance.Status.ERROR
                instance.save()
        else:
            logger.warning(f"No handler for service type: {service_type}")

    def _handle_script_task(self, instance: WorkflowInstance, node: dict):
        """Handle script task - execute Python script"""
        properties = node.get('properties', {})
        script = properties.get('script', '')

        try:
            # Execute script in restricted environment
            local_vars = {'instance': instance, 'variables': instance.variables}
            exec(script, {"__builtins__": {}}, local_vars)
            instance.variables.update(local_vars.get('variables', {}))
            instance.save()
            self._complete_node(instance, node['id'])
            self._move_to_next(instance, node['id'])
        except Exception as e:
            logger.error(f"Script task failed: {e}")
            instance.status = WorkflowInstance.Status.ERROR
            instance.save()

    def _handle_exclusive_gateway(self, instance: WorkflowInstance, node: dict):
        """Handle exclusive gateway - evaluate conditions"""
        edges = instance.definition.get_outgoing_edges(node['id'])

        for edge in edges:
            condition = edge.get('condition', '')
            if self._evaluate_condition(condition, instance.variables):
                self._complete_node(instance, node['id'])
                self._activate_node(instance, edge['target'])
                self._process_node(instance, edge['target'])
                return

        # Default path if no condition matched
        if edges:
            self._complete_node(instance, node['id'])
            self._activate_node(instance, edges[0]['target'])
            self._process_node(instance, edges[0]['target'])

    def _handle_parallel_gateway(self, instance: WorkflowInstance, node: dict):
        """Handle parallel gateway - activate all outgoing paths"""
        edges = instance.definition.get_outgoing_edges(node['id'])
        self._complete_node(instance, node['id'])

        for edge in edges:
            self._activate_node(instance, edge['target'])
            self._process_node(instance, edge['target'])

    def _handle_sub_process(self, instance: WorkflowInstance, node: dict):
        """Handle sub-process - start nested workflow"""
        properties = node.get('properties', {})
        sub_workflow_id = properties.get('subWorkflowId')

        if sub_workflow_id:
            try:
                sub_def = WorkflowDefinition.objects.get(id=sub_workflow_id)
                sub_instance = self.start_instance(
                    sub_def, 
                    variables=instance.variables,
                    entity_type='workflow_instance',
                    entity_id=str(instance.id)
                )
                instance.variables[f"{node['id']}_sub_instance"] = str(sub_instance.id)
                instance.save()
            except WorkflowDefinition.DoesNotExist:
                logger.error(f"Sub-workflow {sub_workflow_id} not found")

    def _evaluate_condition(self, condition: str, variables: dict) -> bool:
        """Evaluate a condition expression"""
        if not condition:
            return True
        try:
            return eval(condition, {"__builtins__": {}}, variables)
        except:
            return False

    def _complete_node(self, instance: WorkflowInstance, node_id: str):
        """Mark node as completed"""
        if node_id not in instance.completed_nodes:
            instance.completed_nodes.append(node_id)
        if node_id in instance.current_nodes:
            instance.current_nodes.remove(node_id)
        instance.save()

    def _activate_node(self, instance: WorkflowInstance, node_id: str):
        """Activate a node"""
        if node_id not in instance.current_nodes:
            instance.current_nodes.append(node_id)
        instance.save()

    def _move_to_next(self, instance: WorkflowInstance, node_id: str):
        """Move to next nodes"""
        edges = instance.definition.get_outgoing_edges(node_id)
        for edge in edges:
            self._activate_node(instance, edge['target'])
            self._process_node(instance, edge['target'])

    def complete_task(self, task: WorkflowTask, form_data: dict, user):
        """Complete a user task and continue workflow"""
        task.status = WorkflowTask.Status.COMPLETED
        task.form_data = form_data
        task.completed_at = __import__('django.utils.timezone').now()
        task.save()

        instance = task.instance
        instance.variables.update(form_data)
        instance.save()

        # Move to next nodes
        self._complete_node(instance, task.node_id)
        self._move_to_next(instance, task.node_id)

        logger.info(f"Task {task.id} completed by {user}")


# Global engine instance
workflow_engine = WorkflowEngine()
