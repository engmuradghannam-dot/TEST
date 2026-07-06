"""Auto-generated module router for apps.projects."""
from rest_framework.routers import DefaultRouter
from apps.projects.views import ProjectViewSet, TaskViewSet, MilestoneViewSet, StakeholderViewSet, RiskRegisterViewSet, IssueLogViewSet, ChangeRequestViewSet, TimeEntryViewSet, TaskCommentViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'milestones', MilestoneViewSet)
router.register(r'stakeholders', StakeholderViewSet)
router.register(r'risk-registers', RiskRegisterViewSet)
router.register(r'issue-logs', IssueLogViewSet)
router.register(r'change-requests', ChangeRequestViewSet)
router.register(r'time-entrys', TimeEntryViewSet)
router.register(r'task-comments', TaskCommentViewSet)

urlpatterns = router.urls
