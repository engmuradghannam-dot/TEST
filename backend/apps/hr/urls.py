"""Auto-generated module router for apps.hr."""
from rest_framework.routers import DefaultRouter
from apps.hr.views import EmployeeViewSet, DepartmentViewSet, TeamViewSet, LeaveRequestViewSet, PayrollViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'payrolls', PayrollViewSet)

urlpatterns = router.urls
