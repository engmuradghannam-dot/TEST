"""Auto-generated module router for apps.inventory."""
from rest_framework.routers import DefaultRouter
from apps.inventory.views import ItemViewSet, ItemGroupViewSet, StockEntryViewSet, ItemSerialNumberViewSet, ItemBatchViewSet, StockReconciliationViewSet, StockReconciliationItemViewSet

router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'item-groups', ItemGroupViewSet)
router.register(r'stock-entrys', StockEntryViewSet)
router.register(r'item-serial-numbers', ItemSerialNumberViewSet)
router.register(r'item-batchs', ItemBatchViewSet)
router.register(r'stock-reconciliations', StockReconciliationViewSet)
router.register(r'stock-reconciliation-items', StockReconciliationItemViewSet)

urlpatterns = router.urls
