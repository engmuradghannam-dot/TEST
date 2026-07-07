from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EventStoreViewSet, EventProjectionViewSet,
    EventHandlerViewSet, EventSubscriptionViewSet,
    SagaInstanceViewSet, DeadLetterQueueViewSet
)

router = DefaultRouter()
router.register(r'events', EventStoreViewSet, basename='event-store')
router.register(r'projections', EventProjectionViewSet, basename='event-projection')
router.register(r'handlers', EventHandlerViewSet, basename='event-handler')
router.register(r'subscriptions', EventSubscriptionViewSet, basename='event-subscription')
router.register(r'sagas', SagaInstanceViewSet, basename='saga-instance')
router.register(r'dlq', DeadLetterQueueViewSet, basename='dead-letter-queue')

urlpatterns = [
    path('', include(router.urls)),
]
