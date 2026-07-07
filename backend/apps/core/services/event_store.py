"""
Nexus Event Store Service
Implements Event Sourcing Pattern with Kafka integration
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic

from apps.core.models import EventStore, AggregateSnapshot, OutboxEvent

class EventStoreService:
    """Central event store for all domain events"""

    def __init__(self):
        self.kafka_producer = None
        self._init_kafka()

    def _init_kafka(self):
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=5,
            enable_idempotence=True
        )

    def append_event(
        self,
        aggregate_id: uuid.UUID,
        aggregate_type: str,
        event_type: str,
        event_data: Dict[str, Any],
        metadata: Optional[Dict] = None,
        tenant_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        correlation_id: Optional[uuid.UUID] = None,
        region: Optional[str] = None
    ) -> EventStore:
        """Append a new event to the event store"""

        with transaction.atomic():
            # Get next version for this aggregate
            last_event = EventStore.objects.filter(
                aggregate_id=aggregate_id
            ).order_by('-version').first()

            version = (last_event.version + 1) if last_event else 1

            # Create event
            event = EventStore.objects.create(
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                version=version,
                event_type=event_type,
                event_data=event_data,
                metadata=metadata or {},
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id or uuid.uuid4(),
                region=region or getattr(settings, 'REGION', 'us-east-1'),
                timestamp=timezone.now()
            )

            # Write to outbox for reliable publishing
            OutboxEvent.objects.create(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload={
                    'event_id': str(event.id),
                    'aggregate_id': str(aggregate_id),
                    'version': version,
                    'event_type': event_type,
                    'event_data': event_data,
                    'metadata': metadata or {},
                    'timestamp': event.timestamp.isoformat(),
                    'region': event.region
                },
                destination_topic=f'nexus-events-{aggregate_type.lower()}',
                partition_key=str(aggregate_id),
                region=event.region
            )

            # Check if snapshot needed
            if version % getattr(settings, 'SNAPSHOT_FREQUENCY', 100) == 0:
                self._create_snapshot(aggregate_id, aggregate_type, version)

            return event

    def get_events(
        self,
        aggregate_id: uuid.UUID,
        from_version: int = 1,
        to_version: Optional[int] = None
    ) -> List[EventStore]:
        """Get events for an aggregate"""
        queryset = EventStore.objects.filter(
            aggregate_id=aggregate_id,
            version__gte=from_version
        ).order_by('version')

        if to_version:
            queryset = queryset.filter(version__lte=to_version)

        return list(queryset)

    def get_all_events(
        self,
        aggregate_type: Optional[str] = None,
        event_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        region: Optional[str] = None,
        tenant_id: Optional[uuid.UUID] = None
    ) -> List[EventStore]:
        """Query events with filters"""
        queryset = EventStore.objects.all()

        if aggregate_type:
            queryset = queryset.filter(aggregate_type=aggregate_type)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if from_timestamp:
            queryset = queryset.filter(timestamp__gte=from_timestamp)
        if to_timestamp:
            queryset = queryset.filter(timestamp__lte=to_timestamp)
        if region:
            queryset = queryset.filter(region=region)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)

        return list(queryset.order_by('timestamp'))

    def _create_snapshot(self, aggregate_id: uuid.UUID, aggregate_type: str, version: int):
        """Create a snapshot of aggregate state"""
        events = self.get_events(aggregate_id)
        state = self._rebuild_state(events)

        AggregateSnapshot.objects.update_or_create(
            aggregate_id=aggregate_id,
            defaults={
                'aggregate_type': aggregate_type,
                'version': version,
                'state': state,
                'region': getattr(settings, 'REGION', 'us-east-1')
            }
        )

    def _rebuild_state(self, events: List[EventStore]) -> Dict:
        """Rebuild aggregate state from events"""
        state = {}
        for event in events:
            state.update(event.event_data)
        return state

    def get_snapshot(self, aggregate_id: uuid.UUID) -> Optional[AggregateSnapshot]:
        """Get latest snapshot for aggregate"""
        return AggregateSnapshot.objects.filter(
            aggregate_id=aggregate_id
        ).order_by('-version').first()

    def replay_events(
        self,
        aggregate_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        handler: Optional[callable] = None
    ):
        """Replay events for recovery or projection rebuild"""
        events = self.get_all_events(
            aggregate_type=aggregate_type,
            from_timestamp=from_timestamp
        )

        for event in events:
            if handler:
                handler(event)
            else:
                self._default_handler(event)

    def _default_handler(self, event: EventStore):
        """Default event handler - publish to Kafka"""
        topic = f'nexus-events-{event.aggregate_type.lower()}'
        self.kafka_producer.send(
            topic,
            key=str(event.aggregate_id),
            value={
                'event_id': str(event.id),
                'aggregate_id': str(event.aggregate_id),
                'version': event.version,
                'event_type': event.event_type,
                'event_data': event.event_data,
                'timestamp': event.timestamp.isoformat(),
                'region': event.region
            }
        )

    def publish_outbox_events(self, batch_size: int = 100):
        """Publish pending outbox events to Kafka"""
        pending = OutboxEvent.objects.filter(
            processed_at__isnull=True,
            retry_count__lt=5
        ).order_by('created_at')[:batch_size]

        for event in pending:
            try:
                self.kafka_producer.send(
                    event.destination_topic,
                    key=event.partition_key or str(event.aggregate_id),
                    value=event.payload
                )
                event.processed_at = timezone.now()
                event.save()
            except Exception as e:
                event.retry_count += 1
                event.error = str(e)
                event.save()


class SagaOrchestrator:
    """Saga pattern for distributed transactions"""

    def __init__(self):
        self.event_store = EventStoreService()

    def start_saga(
        self,
        saga_type: str,
        steps: List[Dict],
        context: Dict,
        tenant_id: Optional[uuid.UUID] = None
    ) -> 'SagaInstance':
        """Start a new saga"""
        from apps.core.models import SagaInstance

        saga = SagaInstance.objects.create(
            saga_type=saga_type,
            status='started',
            total_steps=len(steps),
            steps_data=steps,
            context=context,
            tenant_id=tenant_id,
            region=getattr(settings, 'REGION', 'us-east-1')
        )

        # Emit saga started event
        self.event_store.append_event(
            aggregate_id=saga.saga_id,
            aggregate_type='saga',
            event_type='saga_started',
            event_data={
                'saga_type': saga_type,
                'total_steps': len(steps),
                'context': context
            },
            tenant_id=tenant_id
        )

        return saga

    def execute_step(self, saga_id: uuid.UUID, step_result: Dict):
        """Execute next saga step"""
        from apps.core.models import SagaInstance

        saga = SagaInstance.objects.get(saga_id=saga_id)

        if saga.status in ['completed', 'failed', 'compensated']:
            return saga

        saga.steps_data[saga.current_step]['result'] = step_result
        saga.current_step += 1

        if saga.current_step >= saga.total_steps:
            saga.status = 'completed'
            saga.completed_at = timezone.now()
        else:
            saga.status = 'running'

        saga.save()

        # Emit step completed event
        self.event_store.append_event(
            aggregate_id=saga_id,
            aggregate_type='saga',
            event_type='saga_step_completed',
            event_data={
                'step': saga.current_step - 1,
                'result': step_result,
                'status': saga.status
            }
        )

        return saga

    def compensate(self, saga_id: uuid.UUID, error: str):
        """Trigger saga compensation"""
        from apps.core.models import SagaInstance

        saga = SagaInstance.objects.get(saga_id=saga_id)
        saga.status = 'compensating'
        saga.error_message = error
        saga.save()

        # Execute compensation steps in reverse
        for step in reversed(saga.steps_data[:saga.current_step]):
            if 'compensation' in step:
                # Execute compensation action
                pass

        saga.status = 'compensated'
        saga.save()

        self.event_store.append_event(
            aggregate_id=saga_id,
            aggregate_type='saga',
            event_type='saga_compensated',
            event_data={'error': error}
        )

        return saga


class ProjectionBuilder:
    """Build CQRS read model projections"""

    def __init__(self):
        self.event_store = EventStoreService()

    def build_projection(
        self,
        projection_name: str,
        aggregate_type: str,
        projector: callable,
        from_version: int = 1
    ):
        """Build or rebuild a projection"""
        from apps.core.models import Projection

        events = self.event_store.get_all_events(
            aggregate_type=aggregate_type
        )

        for event in events:
            if event.version < from_version:
                continue

            projection_data = projector(event)

            Projection.objects.update_or_create(
                projection_name=projection_name,
                aggregate_id=event.aggregate_id,
                defaults={
                    'projection_type': aggregate_type,
                    'data': projection_data,
                    'version': event.version,
                    'last_event_timestamp': event.timestamp,
                    'is_stale': False
                }
            )

    def mark_stale(self, projection_name: str, aggregate_id: uuid.UUID):
        """Mark projection as stale when source changes"""
        from apps.core.models import Projection

        Projection.objects.filter(
            projection_name=projection_name,
            aggregate_id=aggregate_id
        ).update(is_stale=True)

    def get_projection(
        self,
        projection_name: str,
        aggregate_id: uuid.UUID
    ) -> Optional[Dict]:
        """Get a projection"""
        from apps.core.models import Projection

        projection = Projection.objects.filter(
            projection_name=projection_name,
            aggregate_id=aggregate_id
        ).first()

        if projection and projection.is_stale:
            # Trigger async rebuild
            pass

        return projection.data if projection else None


class DistributedLockService:
    """Distributed lock for multi-region coordination"""

    def acquire_lock(
        self,
        lock_key: str,
        owner: str,
        ttl_seconds: int = 30
    ) -> bool:
        """Acquire a distributed lock"""
        from apps.core.models import DistributedLock

        now = timezone.now()
        expires_at = now + timedelta(seconds=ttl_seconds)

        # Try to create new lock
        try:
            DistributedLock.objects.create(
                lock_key=lock_key,
                owner=owner,
                expires_at=expires_at,
                region=getattr(settings, 'REGION', 'us-east-1')
            )
            return True
        except:
            # Lock exists, check if expired
            lock = DistributedLock.objects.filter(
                lock_key=lock_key,
                is_released=False
            ).first()

            if lock and lock.expires_at < now:
                # Lock expired, take over
                lock.owner = owner
                lock.expires_at = expires_at
                lock.is_released = False
                lock.save()
                return True

            return False

    def release_lock(self, lock_key: str, owner: str) -> bool:
        """Release a distributed lock"""
        from apps.core.models import DistributedLock

        updated = DistributedLock.objects.filter(
            lock_key=lock_key,
            owner=owner
        ).update(is_released=True)

        return updated > 0

    def extend_lock(self, lock_key: str, owner: str, ttl_seconds: int = 30) -> bool:
        """Extend lock TTL"""
        from apps.core.models import DistributedLock

        expires_at = timezone.now() + timedelta(seconds=ttl_seconds)

        updated = DistributedLock.objects.filter(
            lock_key=lock_key,
            owner=owner,
            is_released=False
        ).update(expires_at=expires_at)

        return updated > 0


class MultiRegionSyncService:
    """Handle cross-region data synchronization"""

    def __init__(self):
        self.event_store = EventStoreService()

    def sync_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        source_region: str,
        target_region: str,
        sync_type: str = 'incremental'
    ):
        """Sync entity across regions"""
        from apps.core.models import MultiRegionSync

        sync_record = MultiRegionSync.objects.create(
            source_region=source_region,
            target_region=target_region,
            sync_type=sync_type,
            entity_type=entity_type,
            entity_id=entity_id,
            data_hash=self._compute_hash(entity_type, entity_id)
        )

        # Emit sync event
        self.event_store.append_event(
            aggregate_id=entity_id,
            aggregate_type=entity_type,
            event_type='cross_region_sync',
            event_data={
                'sync_id': str(sync_record.sync_id),
                'source_region': source_region,
                'target_region': target_region,
                'sync_type': sync_type
            }
        )

        return sync_record

    def _compute_hash(self, entity_type: str, entity_id: uuid.UUID) -> str:
        """Compute hash for conflict detection"""
        import hashlib
        data = f"{entity_type}:{entity_id}"
        return hashlib.sha256(data.encode()).hexdigest()

    def resolve_conflict(
        self,
        sync_id: uuid.UUID,
        resolution: Dict
    ):
        """Resolve sync conflict"""
        from apps.core.models import MultiRegionSync

        sync = MultiRegionSync.objects.get(sync_id=sync_id)
        sync.conflict_detected = True
        sync.conflict_resolution = resolution
        sync.status = 'resolved'
        sync.synced_at = timezone.now()
        sync.save()

        return sync
