"""Auto-generated module router for apps.assets."""
from rest_framework.routers import DefaultRouter
from apps.assets.views import AssetViewSet, AssetCategoryViewSet

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'asset-categories', AssetCategoryViewSet)

urlpatterns = router.urls
