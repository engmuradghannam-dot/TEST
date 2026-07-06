"""Auto-generated module router for apps.workflow."""
from rest_framework.routers import DefaultRouter
from apps.workflow.views import WorkflowViewSet, ApprovalStepViewSet, ApprovalRecordViewSet

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet)
router.register(r'approval-steps', ApprovalStepViewSet)
router.register(r'approval-records', ApprovalRecordViewSet)

urlpatterns = router.urls
