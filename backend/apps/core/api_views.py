"""
API Views for CE-ERP OS
Workflow Engine, AI Brain, Agents, Guidance, Self-Improvement, Plugins
"""
import json
import logging
from typing import Dict, List
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.mixins import CompanyScopedMixin, AuditUserMixin
from apps.core.permissions import IsTenantAdmin, IsTenantManager

from apps.workflow.engine import (
    WorkflowDefinition, ProcessInstance, TaskInstance, ProcessHistory,
    WorkflowEngine, ProcessStatus, TaskStatus, workflow_engine
)
from apps.core.state_machine import (
    StateMachineInstance, StateMachineExecutor, StateMachineRegistry,
    StateTransitionLog
)
from apps.core.ai_brain import (
    AIConversation, AIPromptTemplate, AIKnowledgeBase,
    llm_core, rag_memory, context_engine
)
from apps.core.agent_layer import (
    AgentTask, AgentAction, agent_orchestrator
)
from apps.core.guidance_system import (
    guidance_system, workflow_ai_generator
)
from apps.core.self_improvement import (
    SystemImprovement, PerformanceMetric,
    monitoring_layer, ai_analyzer, suggestion_engine, controlled_deployment
)
from apps.plugins.enhanced_system import (
    PluginRegistry, TenantPlugin, PluginReview, PluginSandbox,
    PluginStatus, PluginLifecycleAction, plugin_lifecycle_manager
)
from apps.core.observability import (
    metrics_collector, alert_manager, HealthCheck, BusinessMetrics
)

logger = logging.getLogger(__name__)


# ============================================================
# Workflow Engine API
# ============================================================

class WorkflowDefinitionViewSet(AuditUserMixin, viewsets.ModelViewSet):
    """Manage BPMN workflow definitions"""
    queryset = WorkflowDefinition.objects.all()
    serializer_class = None  # Would define serializers
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document_type', 'module', 'is_active', 'is_latest']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'version']

    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Create a new version of this workflow"""
        workflow = self.get_object()
        new_version = workflow.create_new_version()
        return Response({
            'id': str(new_version.id),
            'version': new_version.version,
            'message': 'New version created'
        })

    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """Deploy workflow (activate)"""
        workflow = self.get_object()
        workflow.is_active = True
        workflow.save()
        return Response({'status': 'deployed'})

    @action(detail=True, methods=['post'])
    def undeploy(self, request, pk=None):
        """Undeploy workflow (deactivate)"""
        workflow = self.get_object()
        workflow.is_active = False
        workflow.save()
        return Response({'status': 'undeployed'})

    @action(detail=True, methods=['post'])
    def start_instance(self, request, pk=None):
        """Start a new process instance"""
        workflow = self.get_object()
        variables = request.data.get('variables', {})
        context_data = request.data.get('context', {})

        instance = workflow_engine.start_process(
            workflow=workflow,
            variables=variables,
            started_by=request.user,
            tenant_id=str(getattr(request, 'tenant', {}).get('id', '')),
            context_data=context_data
        )

        return Response({
            'instance_id': str(instance.id),
            'status': instance.status,
            'started_at': instance.started_at.isoformat()
        })

    @action(detail=True, methods=['post'])
    def generate_from_ai(self, request, pk=None):
        """Generate workflow from natural language using AI"""
        description = request.data.get('description', '')
        module = request.data.get('module', '')

        if not description:
            return Response({'error': 'Description required'}, status=400)

        workflow_def = workflow_ai_generator.generate_workflow(description, module)

        # Create workflow from AI output
        workflow = WorkflowDefinition.objects.create(
            name=workflow_def.get('name', 'AI Generated'),
            slug=workflow_def.get('name', 'ai-generated').lower().replace(' ', '-'),
            description=workflow_def.get('description', description),
            version=1,
            is_active=True,
            is_latest=True,
            nodes=workflow_def.get('nodes', []),
            edges=workflow_def.get('edges', []),
            document_type=module,
            module=module,
            trigger_types=['api'],
            created_by=request.user
        )

        return Response({
            'workflow_id': str(workflow.id),
            'generated_definition': workflow_def,
            'message': 'Workflow generated by AI'
        })


class ProcessInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """View and manage process instances"""
    queryset = ProcessInstance.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workflow', 'status', 'tenant_id']
    ordering_fields = ['started_at', 'completed_at']

    @action(detail=True, methods=['get'])
    def status_detail(self, request, pk=None):
        """Get detailed process status"""
        instance = self.get_object()
        detail = workflow_engine.get_process_status(str(instance.id))
        return Response(detail)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running process"""
        instance = self.get_object()
        reason = request.data.get('reason', '')
        workflow_engine.cancel_process(str(instance.id), reason)
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        """Complete a user task in the process"""
        instance = self.get_object()
        task_id = request.data.get('task_id')
        form_data = request.data.get('form_data', {})

        if not task_id:
            return Response({'error': 'task_id required'}, status=400)

        result = workflow_engine.complete_user_task(
            task_id=task_id,
            user=request.user,
            form_data=form_data
        )

        return Response(result)


class TaskInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """View and interact with task instances"""
    queryset = TaskInstance.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['process', 'status', 'assigned_to', 'node_type']

    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        """Claim a task for the current user"""
        task = self.get_object()
        task.assigned_to = request.user
        task.save()
        return Response({'status': 'claimed', 'task_id': str(task.id)})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a task with form data"""
        task = self.get_object()
        form_data = request.data.get('form_data', {})

        result = workflow_engine.complete_user_task(
            task_id=str(task.id),
            user=request.user,
            form_data=form_data
        )

        return Response(result)


# ============================================================
# State Machine API
# ============================================================

class StateMachineViewSet(viewsets.ViewSet):
    """State machine operations"""

    @action(detail=False, methods=['get'])
    def definitions(self, request):
        """List all registered state machine definitions"""
        definitions = []
        for doc_type in StateMachineRegistry.list_document_types():
            sm = StateMachineRegistry.get(doc_type)
            definitions.append({
                'document_type': doc_type,
                'name': sm.name,
                'states': list(sm.states),
                'initial_state': sm.initial_state,
                'final_states': list(sm.final_states)
            })
        return Response(definitions)

    @action(detail=False, methods=['get'])
    def available_actions(self, request):
        """Get available actions for a document"""
        document_type = request.query_params.get('document_type')
        document_id = request.query_params.get('document_id')

        if not document_type or not document_id:
            return Response({'error': 'document_type and document_id required'}, status=400)

        try:
            instance = StateMachineInstance.objects.get(
                document_type=document_type,
                document_id=document_id
            )
        except StateMachineInstance.DoesNotExist:
            return Response({'error': 'State machine instance not found'}, status=404)

        sm_def = StateMachineRegistry.get(document_type)
        if not sm_def:
            return Response({'error': 'State machine definition not found'}, status=404)

        executor = StateMachineExecutor(sm_def)
        actions = executor.get_available_actions(instance, request.user)

        return Response({
            'current_state': instance.current_state,
            'available_actions': actions
        })

    @action(detail=False, methods=['post'])
    def transition(self, request):
        """Execute a state transition"""
        document_type = request.data.get('document_type')
        document_id = request.data.get('document_id')
        action = request.data.get('action')
        context = request.data.get('context', {})

        if not all([document_type, document_id, action]):
            return Response({'error': 'document_type, document_id, and action required'}, status=400)

        try:
            instance = StateMachineInstance.objects.get(
                document_type=document_type,
                document_id=document_id
            )
        except StateMachineInstance.DoesNotExist:
            return Response({'error': 'State machine instance not found'}, status=404)

        sm_def = StateMachineRegistry.get(document_type)
        if not sm_def:
            return Response({'error': 'State machine definition not found'}, status=404)

        executor = StateMachineExecutor(sm_def)
        success, message, log = executor.transition(
            instance=instance,
            action=action,
            user=request.user,
            context=context
        )

        return Response({
            'success': success,
            'message': message,
            'new_state': instance.current_state if success else instance.previous_state,
            'log_id': str(log.id) if log else None
        })


# ============================================================
# AI Brain API
# ============================================================

class AIConversationViewSet(viewsets.ModelViewSet):
    """AI conversation management"""
    queryset = AIConversation.objects.all()

    def get_queryset(self):
        return AIConversation.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to the AI assistant"""
        conversation = self.get_object()
        message = request.data.get('message', '')
        current_page = request.data.get('current_page', '')
        context_data = request.data.get('context', {})

        if not message:
            return Response({'error': 'Message required'}, status=400)

        response = guidance_system.process_message(
            message=message,
            user=request.user,
            conversation_id=str(conversation.id),
            current_page=current_page,
            context_data=context_data
        )

        return Response(response)

    @action(detail=False, methods=['post'])
    def quick_ask(self, request):
        """Quick AI query without conversation history"""
        message = request.data.get('message', '')
        module = request.data.get('module', '')

        if not message:
            return Response({'error': 'Message required'}, status=400)

        # Build context
        user_ctx = context_engine.build_user_context(request.user)
        company_ctx = None
        if request.user.company:
            company_ctx = context_engine.build_company_context(request.user.company)

        system_prompt = context_engine.build_system_context(user_ctx, company_ctx)
        if module:
            system_prompt += f"\n\nModule Context: {context_engine.get_module_context(module)}"

        # Check RAG for relevant info
        knowledge = rag_memory.query(
            "company_knowledge",
            message,
            tenant_id=user_ctx.company_id
        )

        prompt = f"""User question: {message}

Relevant context from knowledge base:
{chr(10).join([k['text'] for k in knowledge[:3]])}

Please provide a helpful response."""

        response = llm_core.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )

        return Response({
            'response': response['text'],
            'sources': knowledge[:3],
            'tokens_used': response.get('tokens_used', 0)
        })


class AIPromptTemplateViewSet(AuditUserMixin, viewsets.ModelViewSet):
    """Manage AI prompt templates"""
    queryset = AIPromptTemplate.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['module', 'is_active']
    search_fields = ['name', 'description']

    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """Render template with variables"""
        template = self.get_object()
        variables = request.data.get('variables', {})

        system_prompt, user_prompt = template.render(variables)

        return Response({
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'variables_used': list(variables.keys())
        })

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Render and execute template"""
        template = self.get_object()
        variables = request.data.get('variables', {})

        system_prompt, user_prompt = template.render(variables)

        response = llm_core.generate(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

        return Response({
            'response': response['text'],
            'tokens_used': response.get('tokens_used', 0)
        })


# ============================================================
# Agent API
# ============================================================

class AgentViewSet(viewsets.ViewSet):
    """AI Agent operations"""

    @action(detail=False, methods=['get'])
    def capabilities(self, request):
        """List all agent capabilities"""
        return Response(agent_orchestrator.get_agent_capabilities())

    @action(detail=False, methods=['post'])
    def dispatch(self, request):
        """Dispatch a task to an agent"""
        agent_type = request.data.get('agent_type')
        action = request.data.get('action')
        parameters = request.data.get('parameters', {})

        if not agent_type or not action:
            return Response({'error': 'agent_type and action required'}, status=400)

        try:
            agent_action = AgentAction(action)
        except ValueError:
            return Response({'error': f'Invalid action: {action}'}, status=400)

        task = AgentTask(
            task_id=str(__import__('uuid').uuid4()),
            agent_type=agent_type,
            action=agent_action,
            target_module=parameters.get('module', agent_type),
            target_id=parameters.get('target_id'),
            parameters=parameters
        )

        result = agent_orchestrator.dispatch(task)
        return Response(result)

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """Broadcast a task to multiple agents"""
        action = request.data.get('action')
        parameters = request.data.get('parameters', {})
        target_modules = request.data.get('target_modules', None)

        try:
            agent_action = AgentAction(action)
        except ValueError:
            return Response({'error': f'Invalid action: {action}'}, status=400)

        results = agent_orchestrator.broadcast(agent_action, parameters, target_modules)
        return Response(results)


# ============================================================
# Workflow AI Generator API
# ============================================================

class WorkflowAIGeneratorViewSet(viewsets.ViewSet):
    """AI-powered workflow generation"""

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate workflow from natural language"""
        description = request.data.get('description', '')
        module = request.data.get('module', '')

        if not description:
            return Response({'error': 'Description required'}, status=400)

        result = workflow_ai_generator.generate_workflow(description, module)
        return Response(result)

    @action(detail=False, methods=['post'])
    def explain(self, request):
        """Explain a workflow in human terms"""
        workflow_json = request.data.get('workflow', {})

        if not workflow_json:
            return Response({'error': 'Workflow JSON required'}, status=400)

        explanation = workflow_ai_generator.explain_workflow(workflow_json)
        return Response({'explanation': explanation})

    @action(detail=False, methods=['post'])
    def suggest_improvements(self, request):
        """Suggest improvements to a workflow"""
        workflow_json = request.data.get('workflow', {})

        if not workflow_json:
            return Response({'error': 'Workflow JSON required'}, status=400)

        suggestions = workflow_ai_generator.suggest_improvements(workflow_json)
        return Response({'suggestions': suggestions})


# ============================================================
# Self-Improvement API
# ============================================================

class SelfImprovementViewSet(viewsets.ReadOnlyModelViewSet):
    """System improvement management"""
    queryset = SystemImprovement.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['improvement_type', 'status']
    search_fields = ['title', 'description']

    @action(detail=False, methods=['post'])
    def analyze_system(self, request):
        """Trigger system analysis"""
        # Get metrics
        metrics = monitoring_layer.analyze_trends('workflow_completion_time', hours=24)
        bottlenecks = monitoring_layer.detect_bottlenecks()

        return Response({
            'metrics': metrics,
            'bottlenecks': bottlenecks,
            'message': 'System analysis completed'
        })

    @action(detail=False, methods=['post'])
    def generate_suggestions(self, request):
        """Generate improvement suggestions"""
        analysis_type = request.data.get('analysis_type', 'workflows')

        if analysis_type == 'workflows':
            workflow_data = request.data.get('workflow_data', [])
            analysis = ai_analyzer.analyze_workflows(workflow_data)
        elif analysis_type == 'errors':
            error_logs = request.data.get('error_logs', [])
            analysis = ai_analyzer.analyze_errors(error_logs)
        else:
            return Response({'error': 'Unknown analysis type'}, status=400)

        # Generate suggestions
        from apps.core.self_improvement import ImprovementType
        suggestion = suggestion_engine.generate_suggestion(
            analysis,
            ImprovementType.WORKFLOW_OPTIMIZATION
        )

        # Create improvement record
        improvement = SystemImprovement.objects.create(
            title=suggestion['suggestion'].get('title', 'AI Suggestion'),
            description=suggestion['suggestion'].get('description', ''),
            improvement_type=ImprovementType.WORKFLOW_OPTIMIZATION.value,
            status='detected',
            analysis_data=analysis,
            suggestion_data=suggestion,
            expected_impact=suggestion['suggestion'].get('expected_impact', ''),
            implementation_steps=suggestion['suggestion'].get('implementation_steps', []),
            risk_assessment=suggestion['suggestion'].get('risk', ''),
            rollback_plan=suggestion['suggestion'].get('rollback_plan', '')
        )

        return Response({
            'improvement_id': str(improvement.id),
            'suggestion': suggestion
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an improvement for deployment"""
        improvement = self.get_object()
        improvement.status = 'approved'
        improvement.approved_by = request.user
        improvement.approved_at = timezone.now()
        improvement.save()

        return Response({
            'status': 'approved',
            'improvement_id': str(improvement.id)
        })

    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """Deploy an approved improvement"""
        improvement = self.get_object()

        if improvement.status != 'approved':
            return Response({'error': 'Improvement must be approved first'}, status=400)

        improvement.status = 'deployed'
        improvement.deployed_at = timezone.now()
        improvement.save()

        return Response({
            'status': 'deployed',
            'improvement_id': str(improvement.id)
        })

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback a deployed improvement"""
        improvement = self.get_object()

        improvement.status = 'rolled_back'
        improvement.rolled_back_at = timezone.now()
        improvement.save()

        return Response({
            'status': 'rolled_back',
            'improvement_id': str(improvement.id)
        })


# ============================================================
# Plugin System API
# ============================================================

class PluginRegistryViewSet(viewsets.ReadOnlyModelViewSet):
    """Plugin marketplace/registry"""
    queryset = PluginRegistry.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_published', 'is_premium', 'status']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['download_count', 'rating', 'created_at']

    @action(detail=True, methods=['post'])
    def install(self, request, pk=None):
        """Install a plugin for current tenant"""
        plugin = self.get_object()
        tenant = getattr(request, 'tenant', None)

        if not tenant:
            return Response({'error': 'Tenant required'}, status=400)

        config = request.data.get('config', {})
        result = plugin_lifecycle_manager.install(plugin, tenant, config, request.user)

        return Response(result)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Add a review for a plugin"""
        plugin = self.get_object()
        rating = request.data.get('rating')
        title = request.data.get('title', '')
        review_text = request.data.get('review', '')

        if not rating or not (1 <= rating <= 5):
            return Response({'error': 'Rating must be 1-5'}, status=400)

        review, created = PluginReview.objects.update_or_create(
            plugin=plugin,
            user=request.user,
            defaults={
                'rating': rating,
                'title': title,
                'review': review_text
            }
        )

        # Update plugin rating
        reviews = plugin.reviews.all()
        plugin.rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
        plugin.review_count = len(reviews)
        plugin.save()

        return Response({
            'review_id': str(review.id),
            'created': created,
            'new_rating': plugin.rating
        })


class TenantPluginViewSet(viewsets.ModelViewSet):
    """Manage tenant plugins"""
    queryset = TenantPlugin.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'plugin']

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            return TenantPlugin.objects.filter(tenant=tenant)
        return TenantPlugin.objects.none()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a plugin"""
        tp = self.get_object()
        result = plugin_lifecycle_manager.activate(tp, request.user)
        return Response(result)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a plugin"""
        tp = self.get_object()
        result = plugin_lifecycle_manager.deactivate(tp, request.user)
        return Response(result)

    @action(detail=True, methods=['post'])
    def uninstall(self, request, pk=None):
        """Uninstall a plugin"""
        tp = self.get_object()
        result = plugin_lifecycle_manager.uninstall(tp, request.user)
        return Response(result)

    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None):
        """Update plugin configuration"""
        tp = self.get_object()
        tp.config = request.data.get('config', tp.config)
        tp.save()
        return Response({'status': 'updated', 'config': tp.config})


# ============================================================
# Observability API
# ============================================================

class ObservabilityViewSet(viewsets.ViewSet):
    """System observability endpoints"""

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get all metrics in Prometheus format"""
        metrics_text = metrics_collector.get_metrics()
        return Response(metrics_text, content_type='text/plain')

    @action(detail=False, methods=['get'])
    def business_metrics(self, request):
        """Get business metrics as JSON"""
        return Response(metrics_collector.get_business_metrics())

    @action(detail=False, methods=['get'])
    def health(self, request):
        """System health check"""
        health = HealthCheck.check_all()
        overall = 'healthy' if all(h.get('status') == 'healthy' for h in health.values() if isinstance(h, dict)) else 'unhealthy'
        return Response({
            'status': overall,
            'checks': health
        })

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get current alerts"""
        metrics = metrics_collector.get_business_metrics()
        # Flatten metrics for alert checking
        flat_metrics = {}
        for category, values in metrics.items():
            if isinstance(values, dict):
                for key, val in values.items():
                    if isinstance(val, (int, float)):
                        flat_metrics[f"{category}.{key}"] = val

        alerts = alert_manager.check_all(flat_metrics)
        return Response({'alerts': alerts})

    @action(detail=False, methods=['post'])
    def record_metric(self, request):
        """Record a custom metric"""
        metric_type = request.data.get('type', 'counter')
        name = request.data.get('name')
        value = request.data.get('value', 1)
        tags = request.data.get('tags', {})

        if not name:
            return Response({'error': 'Metric name required'}, status=400)

        if metric_type == 'counter':
            metrics_collector.counter(name, value, tags)
        elif metric_type == 'gauge':
            metrics_collector.gauge(name, value, tags)
        elif metric_type == 'histogram':
            metrics_collector.histogram(name, value, tags)

        return Response({'status': 'recorded'})
