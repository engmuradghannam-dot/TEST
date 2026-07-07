"""
Kafka Event Consumers for Nexus Framework
"""
import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from django.conf import settings

logger = logging.getLogger(__name__)

class EventBus:
    """Central event bus using Kafka"""

    def __init__(self):
        self.producer = None
        self.consumer = None
        self._connect()

    def _connect(self):
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests=5,
            compression_type='lz4'
        )

        logger.info("Kafka producer connected")

    def publish(self, topic, event, key=None, headers=None):
        """Publish event to Kafka topic"""
        try:
            future = self.producer.send(
                topic,
                key=key,
                value=event,
                headers=headers or {}
            )
            record_metadata = future.get(timeout=10)
            logger.info(f"Published to {topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            return record_metadata
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            raise

    def publish_async(self, topic, event, key=None, headers=None):
        """Async publish with callback"""
        def on_send_success(record_metadata):
            logger.debug(f"Message delivered to {record_metadata.topic}")

        def on_send_error(excp):
            logger.error(f"Message delivery failed: {excp}")

        self.producer.send(
            topic,
            key=key,
            value=event,
            headers=headers or {}
        ).add_callback(on_send_success).add_errback(on_send_error)

    def create_consumer(self, group_id, topics, auto_offset_reset='latest'):
        """Create a Kafka consumer"""
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=False,
            max_poll_records=500,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda m: m.decode('utf-8') if m else None
        )

        return consumer

    def close(self):
        """Close connections"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
        if self.consumer:
            self.consumer.close()


# Domain event definitions
class DomainEvents:
    """Domain event constants and schemas"""

    # User events
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'
    USER_LOGGED_IN = 'user.logged_in'

    # Company events
    COMPANY_CREATED = 'company.created'
    COMPANY_UPDATED = 'company.updated'
    COMPANY_DELETED = 'company.deleted'

    # Industry events
    INDUSTRY_DEPLOYED = 'industry.deployed'
    CONTROL_ACTIVATED = 'control.activated'
    CONTROL_EXECUTED = 'control.executed'

    # Compliance events
    COMPLIANCE_CHECK_PASSED = 'compliance.check_passed'
    COMPLIANCE_CHECK_FAILED = 'compliance.check_failed'
    AUDIT_COMPLETED = 'audit.completed'

    # Financial events
    INVOICE_CREATED = 'invoice.created'
    PAYMENT_RECEIVED = 'payment.received'
    PAYMENT_FAILED = 'payment.failed'

    # Inventory events
    STOCK_MOVED = 'stock.moved'
    STOCK_LOW = 'stock.low'
    REORDER_TRIGGERED = 'reorder.triggered'

    # HR events
    EMPLOYEE_HIRED = 'employee.hired'
    EMPLOYEE_TERMINATED = 'employee.terminated'
    PAYROLL_PROCESSED = 'payroll.processed'

    # Integration events
    WEBHOOK_DELIVERED = 'webhook.delivered'
    WEBHOOK_FAILED = 'webhook.failed'
    SYNC_COMPLETED = 'sync.completed'


# Event handlers registry
class EventHandlerRegistry:
    """Registry for event handlers"""

    _handlers = {}

    @classmethod
    def register(cls, event_name, handler_func):
        if event_name not in cls._handlers:
            cls._handlers[event_name] = []
        cls._handlers[event_name].append(handler_func)
        logger.info(f"Registered handler for {event_name}")

    @classmethod
    def get_handlers(cls, event_name):
        return cls._handlers.get(event_name, [])

    @classmethod
    def handle(cls, event_name, event_data):
        handlers = cls.get_handlers(event_name)
        results = []
        for handler in handlers:
            try:
                result = handler(event_data)
                results.append({'handler': handler.__name__, 'success': True, 'result': result})
            except Exception as e:
                results.append({'handler': handler.__name__, 'success': False, 'error': str(e)})
        return results


# Decorator for registering handlers
def event_handler(event_name):
    def decorator(func):
        EventHandlerRegistry.register(event_name, func)
        return func
    return decorator


# Example handlers
@event_handler(DomainEvents.USER_CREATED)
def handle_user_created(event_data):
    """Send welcome email when user is created"""
    from apps.core.models import User
    user_id = event_data.get('user_id')
    # Send welcome email
    logger.info(f"Sending welcome email to user {user_id}")
    return {'email_sent': True}

@event_handler(DomainEvents.STOCK_LOW)
def handle_stock_low(event_data):
    """Trigger reorder when stock is low"""
    from apps.inventory.models import Item
    item_id = event_data.get('item_id')
    # Trigger reorder
    logger.info(f"Triggering reorder for item {item_id}")
    return {'reorder_triggered': True}

@event_handler(DomainEvents.COMPLIANCE_CHECK_FAILED)
def handle_compliance_failed(event_data):
    """Alert when compliance check fails"""
    control_id = event_data.get('control_id')
    company_id = event_data.get('company_id')
    logger.warning(f"Compliance check failed: {control_id} for company {company_id}")
    return {'alert_sent': True}
