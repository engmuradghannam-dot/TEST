from celery import shared_task
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_event(self, event_id):
    """Process an event from the event store"""
    from .models import EventStore, EventHandler, DeadLetterQueue

    try:
        event = EventStore.objects.get(event_id=event_id)

        # Find matching handlers
        handlers = EventHandler.objects.filter(
            event_names__contains=[event.event_name],
            status='active',
            is_active=True
        )

        for handler in handlers:
            try:
                # Execute handler logic
                # In real implementation, this would call the actual handler function
                handler.processed_count += 1
                handler.last_processed_at = timezone.now()
                handler.save()

                logger.info(f"Event {event_id} processed by handler {handler.handler_id}")

            except Exception as e:
                handler.failed_count += 1
                handler.save()

                # Create DLQ entry
                DeadLetterQueue.objects.create(
                    original_event=event,
                    error_message=str(e),
                    error_stack=traceback.format_exc(),
                    handler_id=handler.handler_id
                )

                logger.error(f"Handler {handler.handler_id} failed for event {event_id}: {e}")

        # Update event as processed
        event.processed = True
        event.processed_at = timezone.now()
        event.save()

        # Update projections
        update_projection.delay(event.aggregate_type, event.aggregate_id)

    except EventStore.DoesNotExist:
        logger.error(f"Event {event_id} not found")
    except Exception as e:
        logger.error(f"Failed to process event {event_id}: {e}")
        self.retry(exc=e)

@shared_task
def update_projection(aggregate_type, aggregate_id):
    """Update read model projections"""
    from .models import EventStore, EventProjection

    # Get all events for this aggregate
    events = EventStore.objects.filter(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id
    ).order_by('version')

    # Rebuild projection state
    state = {}
    for event in events:
        # Apply event to state
        if event.event_name == 'created':
            state = event.payload
        elif event.event_name == 'updated':
            state.update(event.payload)
        elif event.event_name == 'deleted':
            state = {'deleted': True, 'deleted_at': str(event.timestamp)}

    # Update or create projection
    projection, created = EventProjection.objects.update_or_create(
        projection_name=f"{aggregate_type}_default",
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        defaults={
            'state': state,
            'version': events.count(),
            'is_stale': False,
            'last_event_timestamp': events.last().timestamp if events.exists() else None
        }
    )

    logger.info(f"Projection updated for {aggregate_type}:{aggregate_id}")

@shared_task(bind=True, max_retries=5)
def deliver_webhook(self, subscription_id, event_id):
    """Deliver event to webhook subscription"""
    from .models import EventSubscription, EventStore
    import requests

    try:
        subscription = EventSubscription.objects.get(subscription_id=subscription_id)
        event = EventStore.objects.get(event_id=event_id)

        response = requests.post(
            subscription.endpoint,
            json={
                'event_id': str(event.event_id),
                'event_name': event.event_name,
                'aggregate_type': event.aggregate_type,
                'aggregate_id': event.aggregate_id,
                'payload': event.payload,
                'timestamp': str(event.timestamp)
            },
            headers={
                **subscription.headers,
                'X-Event-ID': str(event.event_id),
                'X-Event-Name': event.event_name,
                'X-Signature': 'sha256=' + generate_signature(event.payload, subscription.headers.get('X-Secret', ''))
            },
            timeout=subscription.timeout_seconds
        )

        if response.status_code >= 400:
            raise Exception(f"Webhook returned {response.status_code}: {response.text}")

        subscription.delivery_count += 1
        subscription.last_delivered_at = timezone.now()
        subscription.save()

    except requests.RequestException as e:
        logger.error(f"Webhook delivery failed: {e}")
        self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    except Exception as e:
        logger.error(f"Unexpected error in webhook delivery: {e}")
        raise

def generate_signature(payload, secret):
    import hmac
    import hashlib
    import json

    message = json.dumps(payload, sort_keys=True)
    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

@shared_task
def compensate_saga(saga_id):
    """Execute saga compensation"""
    from .models import SagaInstance

    saga = SagaInstance.objects.get(saga_id=saga_id)
    saga.state = 'compensating'
    saga.save()

    # Execute compensation steps in reverse order
    steps = saga.steps_log[::-1]
    for step in steps:
        if step.get('compensation'):
            # Execute compensation action
            logger.info(f"Compensating step {step['step']} for saga {saga_id}")
            # Real implementation would call compensation service

    saga.state = 'compensated'
    saga.completed_at = timezone.now()
    saga.save()

    logger.info(f"Saga {saga_id} compensated successfully")

@shared_task
def cleanup_old_events(days=90):
    """Archive events older than specified days"""
    from .models import EventStore
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=days)
    old_events = EventStore.objects.filter(timestamp__lt=cutoff, processed=True)

    # Archive to cold storage (S3, etc.)
    # In real implementation, this would move to S3 Glacier
    count = old_events.count()
    old_events.delete()

    logger.info(f"Cleaned up {count} old events")
    return count
