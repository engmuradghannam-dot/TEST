from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    EventStore, EventProjection, EventHandler,
    EventSubscription, SagaInstance, DeadLetterQueue
)
from .serializers import (
    EventStoreSerializer, EventStoreCreateSerializer,
    EventProjectionSerializer, EventHandlerSerializer,
    EventSubscriptionSerializer, SagaInstanceSerializer,
    DeadLetterQueueSerializer
)

class EventStoreViewSet(viewsets.ModelViewSet):
    """Event Sourcing - Immutable event log"""
    queryset = EventStore.objects.all()
    serializer_class = EventStoreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'aggregate_type', 'event_name', 'processed', 'tenant_id', 'region']
    search_fields = ['event_name', 'aggregate_type', 'aggregate_id']
    ordering_fields = ['timestamp', 'version']
    lookup_field = 'event_id'

    def get_serializer_class(self):
        if self.action == 'create':
            return EventStoreCreateSerializer
        return EventStoreSerializer

    @action(detail=False, methods=['post'])
    def publish(self, request):
        """Publish a new event to the event store"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get latest version for this aggregate
        latest = EventStore.objects.filter(
            aggregate_type=serializer.validated_data['aggregate_type'],
            aggregate_id=serializer.validated_data['aggregate_id']
        ).order_by('-version').first()

        version = (latest.version + 1) if latest else 1

        event = EventStore.objects.create(
            **serializer.validated_data,
            version=version,
            region=request.headers.get('X-Region', 'us-east-1')
        )

        # Trigger async processing
        from .tasks import process_event
        process_event.delay(str(event.event_id))

        return Response({
            'success': True,
            'event_id': str(event.event_id),
            'version': version
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_aggregate(self, request):
        """Get all events for a specific aggregate"""
        aggregate_type = request.query_params.get('aggregate_type')
        aggregate_id = request.query_params.get('aggregate_id')

        if not aggregate_type or not aggregate_id:
            return Response({'error': 'aggregate_type and aggregate_id required'}, status=400)

        events = self.queryset.filter(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id
        ).order_by('version')

        return Response({
            'aggregate_type': aggregate_type,
            'aggregate_id': aggregate_id,
            'event_count': events.count(),
            'events': EventStoreSerializer(events, many=True).data
        })

    @action(detail=False, methods=['get'])
    def replay(self, request):
        """Replay events to rebuild projections"""
        aggregate_type = request.query_params.get('aggregate_type')
        aggregate_id = request.query_params.get('aggregate_id')
        from_version = int(request.query_params.get('from_version', 1))

        events = self.queryset.filter(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            version__gte=from_version
        ).order_by('version')

        # Mark as unprocessed for replay
        events.update(processed=False, processed_at=None)

        # Trigger replay
        for event in events:
            from .tasks import process_event
            process_event.delay(str(event.event_id))

        return Response({
            'success': True,
            'events_queued': events.count()
        })

    @action(detail=False, methods=['get'])
    def stream(self, request):
        """Server-sent events stream (for real-time updates)"""
        from django.http import StreamingHttpResponse
        import json
        import time

        def event_generator():
            last_id = request.headers.get('Last-Event-ID', '')
            while True:
                events = EventStore.objects.filter(
                    event_id__gt=last_id if last_id else '00000000-0000-0000-0000-000000000000'
                ).order_by('timestamp')[:10]

                for event in events:
                    last_id = str(event.event_id)
                    yield f"data: {json.dumps(EventStoreSerializer(event).data)}\n\n"

                time.sleep(1)

        response = StreamingHttpResponse(event_generator(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class EventProjectionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read model projections"""
    queryset = EventProjection.objects.all()
    serializer_class = EventProjectionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['projection_name', 'aggregate_type', 'is_stale']
    search_fields = ['projection_name', 'aggregate_id']

    @action(detail=True, methods=['post'])
    def rebuild(self, request, pk=None):
        """Rebuild projection from event stream"""
        projection = self.get_object()

        # Get all events for this aggregate
        events = EventStore.objects.filter(
            aggregate_type=projection.aggregate_type,
            aggregate_id=projection.aggregate_id
        ).order_by('version')

        # Rebuild state
        state = {}
        for event in events:
            # Apply event to state (simplified - real would use event handlers)
            state.update(event.payload)

        projection.state = state
        projection.version = events.count()
        projection.is_stale = False
        projection.last_event_timestamp = events.last().timestamp if events.exists() else None
        projection.save()

        return Response({
            'success': True,
            'projection': EventProjectionSerializer(projection).data
        })


class EventHandlerViewSet(viewsets.ModelViewSet):
    """Event handler management"""
    queryset = EventHandler.objects.all()
    serializer_class = EventHandlerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'handler_type', 'is_active']
    search_fields = ['handler_name', 'handler_id']
    lookup_field = 'handler_id'

    @action(detail=True, methods=['post'])
    def pause(self, request, handler_id=None):
        handler = self.get_object()
        handler.status = 'paused'
        handler.save()
        return Response({'success': True, 'status': 'paused'})

    @action(detail=True, methods=['post'])
    def resume(self, request, handler_id=None):
        handler = self.get_object()
        handler.status = 'active'
        handler.save()
        return Response({'success': True, 'status': 'active'})

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get handler metrics"""
        total = self.queryset.count()
        active = self.queryset.filter(status='active').count()
        failed = self.queryset.filter(status='failed').count()
        total_processed = sum(h.processed_count for h in self.queryset.all())
        total_failed = sum(h.failed_count for h in self.queryset.all())

        return Response({
            'total_handlers': total,
            'active': active,
            'failed': failed,
            'total_processed': total_processed,
            'total_failed': total_failed,
            'success_rate': (total_processed / (total_processed + total_failed) * 100) if (total_processed + total_failed) > 0 else 0
        })


class EventSubscriptionViewSet(viewsets.ModelViewSet):
    """External event subscriptions"""
    queryset = EventSubscription.objects.all()
    serializer_class = EventSubscriptionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['subscription_type', 'is_active']
    search_fields = ['name', 'endpoint']

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test subscription endpoint"""
        subscription = self.get_object()

        import requests
        try:
            response = requests.post(
                subscription.endpoint,
                json={'test': True, 'timestamp': str(timezone.now())},
                headers=subscription.headers,
                timeout=subscription.timeout_seconds
            )
            return Response({
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response': response.text[:500]
            })
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)


class SagaInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Saga orchestration instances"""
    queryset = SagaInstance.objects.all()
    serializer_class = SagaInstanceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['saga_type', 'state']
    ordering_fields = ['started_at', 'completed_at']
    lookup_field = 'saga_id'

    @action(detail=True, methods=['post'])
    def compensate(self, request, saga_id=None):
        """Trigger saga compensation"""
        saga = self.get_object()
        if saga.state not in ['running', 'completed']:
            return Response({'error': 'Cannot compensate saga in state: ' + saga.state}, status=400)

        saga.state = 'compensating'
        saga.save()

        # Trigger compensation
        from .tasks import compensate_saga
        compensate_saga.delay(str(saga.saga_id))

        return Response({'success': True, 'message': 'Compensation triggered'})


class DeadLetterQueueViewSet(viewsets.ModelViewSet):
    """Dead letter queue management"""
    queryset = DeadLetterQueue.objects.all()
    serializer_class = DeadLetterQueueSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['resolved', 'handler_id']
    ordering_fields = ['created_at']

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed event"""
        dlq_entry = self.get_object()

        if dlq_entry.resolved:
            return Response({'error': 'Already resolved'}, status=400)

        if dlq_entry.original_event:
            dlq_entry.original_event.processed = False
            dlq_entry.original_event.error_count = 0
            dlq_entry.original_event.last_error = ''
            dlq_entry.original_event.save()

            from .tasks import process_event
            process_event.delay(str(dlq_entry.original_event.event_id))

        dlq_entry.retry_count += 1
        dlq_entry.save()

        return Response({'success': True, 'retry_count': dlq_entry.retry_count})

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark DLQ entry as resolved"""
        dlq_entry = self.get_object()
        dlq_entry.resolved = True
        dlq_entry.resolved_at = timezone.now()
        dlq_entry.resolved_by = request.user if request.user.is_authenticated else None
        dlq_entry.save()
        return Response({'success': True})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """DLQ statistics"""
        total = self.queryset.count()
        resolved = self.queryset.filter(resolved=True).count()
        unresolved = total - resolved

        by_handler = self.queryset.values('handler_id').annotate(
            count=Count('dlq_id')
        ).order_by('-count')[:10]

        return Response({
            'total': total,
            'resolved': resolved,
            'unresolved': unresolved,
            'top_handlers': list(by_handler)
        })
