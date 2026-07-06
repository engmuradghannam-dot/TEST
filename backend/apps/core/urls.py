"""
Nexus CE-ERP OS - API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.core.views import UIScreenViewSet
from apps.core.api_views import (
    WorkflowDefinitionViewSet, ProcessInstanceViewSet, TaskInstanceViewSet,
    StateMachineViewSet, AIConversationViewSet, AIPromptTemplateViewSet,
    AgentViewSet, WorkflowAIGeneratorViewSet, SelfImprovementViewSet,
    PluginRegistryViewSet, TenantPluginViewSet, ObservabilityViewSet
)

router = DefaultRouter()

# Workflow Engine
router.register(r'workflows/definitions', WorkflowDefinitionViewSet, basename='workflow-definition')
router.register(r'workflows/instances', ProcessInstanceViewSet, basename='workflow-instance')
router.register(r'workflows/tasks', TaskInstanceViewSet, basename='workflow-task')

# State Machine
router.register(r'state-machines', StateMachineViewSet, basename='state-machine')

# AI Brain
router.register(r'ai/conversations', AIConversationViewSet, basename='ai-conversation')
router.register(r'ai/prompts', AIPromptTemplateViewSet, basename='ai-prompt')

# Agents
router.register(r'ai/agents', AgentViewSet, basename='ai-agent')

# Workflow AI Generator
router.register(r'ai/workflow-generator', WorkflowAIGeneratorViewSet, basename='ai-workflow-generator')

# Self-Improvement
router.register(r'system/improvements', SelfImprovementViewSet, basename='system-improvement')

# Plugin System
router.register(r'plugins/registry', PluginRegistryViewSet, basename='plugin-registry')
router.register(r'plugins/tenant', TenantPluginViewSet, basename='tenant-plugin')

# Observability
router.register(r'system/observability', ObservabilityViewSet, basename='observability')
router.register(r'ui-screens', UIScreenViewSet, basename='ui-screens')

urlpatterns = [
    path('', include(router.urls)),
]
