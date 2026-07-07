from rest_framework.routers import DefaultRouter
from .views import EventStoreViewSet, EventProjectionViewSet, EventHandlerViewSet, EventSubscriptionViewSet, SagaInstanceViewSet, DeadLetterQueueViewSet

router = DefaultRouter()
router.register(r'event-stores', EventStoreViewSet)
router.register(r'event-projections', EventProjectionViewSet)
router.register(r'event-handlers', EventHandlerViewSet)
router.register(r'event-subscriptions', EventSubscriptionViewSet)
router.register(r'saga-instances', SagaInstanceViewSet)
router.register(r'dead-letter-queues', DeadLetterQueueViewSet)

urlpatterns = router.urls