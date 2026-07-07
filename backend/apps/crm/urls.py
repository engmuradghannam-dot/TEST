"""Auto-generated module router for apps.crm."""
from rest_framework.routers import DefaultRouter
from apps.crm.views import LeadViewSet, OpportunityViewSet

router = DefaultRouter()
router.register(r'leads', LeadViewSet)
router.register(r'opportunities', OpportunityViewSet)

urlpatterns = router.urls
