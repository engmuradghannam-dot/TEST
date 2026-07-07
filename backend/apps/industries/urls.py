from rest_framework.routers import DefaultRouter
from .views import IndustryCatalogViewSet, IndustryControlViewSet, AIAgentRegistryViewSet, CompanyIndustryProfileViewSet, ControlExecutionLogViewSet

router = DefaultRouter()
router.register(r'industry-catalogs', IndustryCatalogViewSet)
router.register(r'industry-controls', IndustryControlViewSet)
router.register(r'a-i-agent-registrys', AIAgentRegistryViewSet)
router.register(r'company-industry-profiles', CompanyIndustryProfileViewSet)
router.register(r'control-execution-logs', ControlExecutionLogViewSet)

urlpatterns = router.urls