"""
Nexus Event Bus - Redis-based Event-Driven Architecture
Supports: pub/sub, streams, delayed events, event persistence
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class DomainEvent:
    """Base class for all domain events"""
    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    tenant_id: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    @classmethod
    def create(cls, event_type: str, aggregate_type: str, aggregate_id: str,
                 tenant_id: str, payload: Dict, priority: EventPriority = EventPriority.NORMAL,
                 correlation_id: Optional[str] = None, causation_id: Optional[str] = None):
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            payload=payload,
            metadata={
                'source': 'nexus-erp',
                'version': '1.0',
                'environment': settings.DEBUG and 'development' or 'production'
            },
            timestamp=datetime.utcnow().isoformat(),
            priority=priority,
            correlation_id=correlation_id or str(uuid.uuid4()),
            causation_id=causation_id
        )

    def to_dict(self):
        data = asdict(self)
        data['priority'] = self.priority.value
        return data

    def to_json(self):
        return json.dumps(self.to_dict())


class EventBus:
    """Redis-based Event Bus with pub/sub and streams support"""

    def __init__(self):
        self._redis = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._handlers: Dict[str, List[Callable]] = {}

    @property
    def redis(self):
        if self._redis is None:
            self._redis = redis.from_url(
                getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
                decode_responses=True
            )
        return self._redis

    def publish(self, event: DomainEvent, delay_seconds: int = 0) -> str:
        """Publish event to bus. Supports delayed delivery."""
        try:
            event_data = event.to_json()
            stream_key = f"nexus:events:{event.aggregate_type}"

            if delay_seconds > 0:
                # Delayed event - use sorted set
                score = (datetime.utcnow() + timedelta(seconds=delay_seconds)).timestamp()
                self.redis.zadd("nexus:events:delayed", {event_data: score})
                logger.info(f"Event {event.event_id} scheduled for delay {delay_seconds}s")
            else:
                # Immediate publish to stream
                self.redis.xadd(stream_key, {"data": event_data})
                # Also publish to pub/sub for real-time subscribers
                self.redis.publish(f"nexus:channel:{event.event_type}", event_data)

            # Persist to event store
            self.redis.xadd("nexus:events:all", {"data": event_data})

            logger.info(f"Event published: {event.event_type} -> {event.aggregate_id}")
            return event.event_id
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Handler subscribed to {event_type}")

    def register_handler(self, event_type: str, handler: Callable):
        """Register persistent handler for event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def process_delayed_events(self):
        """Process events that have reached their delivery time"""
        now = datetime.utcnow().timestamp()
        events = self.redis.zrangebyscore("nexus:events:delayed", 0, now)
        for event_data in events:
            try:
                event_dict = json.loads(event_data)
                event = DomainEvent(**event_dict)
                self.publish(event)
                self.redis.zrem("nexus:events:delayed", event_data)
            except Exception as e:
                logger.error(f"Failed to process delayed event: {e}")

    def read_stream(self, stream_key: str, last_id: str = "0") -> List[Dict]:
        """Read events from stream"""
        messages = self.redis.xread({stream_key: last_id}, block=1000, count=100)
        events = []
        for stream_name, msgs in messages:
            for msg_id, msg_data in msgs:
                events.append({
                    'id': msg_id,
                    'data': json.loads(msg_data.get('data', '{}'))
                })
        return events

    def get_event_store(self, aggregate_type: str, aggregate_id: str, limit: int = 100) -> List[Dict]:
        """Get all events for an aggregate (event sourcing)"""
        stream_key = f"nexus:events:{aggregate_type}"
        messages = self.redis.xrevrange(stream_key, count=limit)
        events = []
        for msg_id, msg_data in messages:
            data = json.loads(msg_data.get('data', '{}'))
            if data.get('aggregate_id') == aggregate_id:
                events.append(data)
        return list(reversed(events))

    def create_consumer_group(self, stream_key: str, group_name: str):
        """Create consumer group for stream processing"""
        try:
            self.redis.xgroup_create(stream_key, group_name, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "already exists" not in str(e):
                raise

    def consume_group(self, stream_key: str, group_name: str, consumer_name: str,
                      count: int = 10, block: int = 5000) -> List[Dict]:
        """Consume events from consumer group"""
        messages = self.redis.xreadgroup(
            group_name, consumer_name, {stream_key: ">"},
            count=count, block=block
        )
        events = []
        for stream_name, msgs in messages:
            for msg_id, msg_data in msgs:
                events.append({
                    'id': msg_id,
                    'data': json.loads(msg_data.get('data', '{}'))
                })
        return events

    def acknowledge(self, stream_key: str, group_name: str, msg_id: str):
        """Acknowledge message processing"""
        self.redis.xack(stream_key, group_name, msg_id)


# Global event bus instance
event_bus = EventBus()


# ============================================================
# Event Types Registry
# ============================================================

class EventTypes:
    # Workflow Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_STEP_EXECUTED = "workflow.step.executed"
    WORKFLOW_APPROVAL_REQUIRED = "workflow.approval.required"
    WORKFLOW_APPROVAL_GRANTED = "workflow.approval.granted"
    WORKFLOW_APPROVAL_REJECTED = "workflow.approval.rejected"

    # State Machine Events
    STATE_TRANSITIONED = "state.transitioned"
    STATE_TRANSITION_FAILED = "state.transition.failed"

    # Business Events
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"
    PURCHASE_ORDER_CREATED = "po.created"
    PURCHASE_ORDER_APPROVED = "po.approved"
    SALES_ORDER_CREATED = "so.created"
    SALES_ORDER_SHIPPED = "so.shipped"
    INVENTORY_LOW_STOCK = "inventory.low_stock"
    INVENTORY_REORDER_TRIGGERED = "inventory.reorder_triggered"
    EMPLOYEE_ONBOARDED = "hr.employee.onboarded"
    LEAVE_REQUESTED = "hr.leave.requested"
    LEAVE_APPROVED = "hr.leave.approved"

    # AI Events
    AI_PREDICTION_MADE = "ai.prediction.made"
    AI_ANOMALY_DETECTED = "ai.anomaly.detected"
    AI_SUGGESTION_GENERATED = "ai.suggestion.generated"
    AI_WORKFLOW_GENERATED = "ai.workflow.generated"

    # Plugin Events
    PLUGIN_INSTALLED = "plugin.installed"
    PLUGIN_UPDATED = "plugin.updated"
    PLUGIN_UNINSTALLED = "plugin.uninstalled"
    PLUGIN_ACTIVATED = "plugin.activated"

    # System Events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    TENANT_CREATED = "tenant.created"
    TENANT_SUSPENDED = "tenant.suspended"
    ERROR_OCCURRED = "system.error"
    METRIC_COLLECTED = "system.metric"
