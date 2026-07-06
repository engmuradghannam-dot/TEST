"""Auto-generated module router for apps.manufacturing."""
from rest_framework.routers import DefaultRouter
from apps.manufacturing.views import WorkOrderViewSet, BOMViewSet, BOMItemViewSet

router = DefaultRouter()
router.register(r'work-orders', WorkOrderViewSet)
router.register(r'b-o-ms', BOMViewSet)
router.register(r'b-o-m-items', BOMItemViewSet)

urlpatterns = router.urls
