"""Workflow module router."""
from rest_framework.routers import DefaultRouter
from apps.workflow.views import (WorkflowViewSet, ApprovalStepViewSet,
                                   ApprovalRecordViewSet, WorkflowStateViewSet,
                                   WorkflowTransitionViewSet)

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet)
router.register(r'workflow-states', WorkflowStateViewSet)
router.register(r'workflow-transitions', WorkflowTransitionViewSet)
router.register(r'approval-steps', ApprovalStepViewSet)
router.register(r'approval-records', ApprovalRecordViewSet)

urlpatterns = router.urls
