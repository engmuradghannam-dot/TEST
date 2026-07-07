from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import uuid

class EventStore(models.Model):
    """Event Sourcing - Immutable event log"""
    EVENT_TYPES = [
        ('domain', 'Domain Event'),
        ('integration', 'Integration Event'),
        ('system', 'System Event'),
        ('audit', 'Audit Event'),
    ]

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='domain')
    aggregate_type = models.CharField(max_length=100, db_index=True)
    aggregate_id = models.CharField(max_length=100, db_index=True)
    event_name = models.CharField(max_length=200, db_index=True)
    payload = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    version = models.PositiveIntegerField(default=1)
    causation_id = models.UUIDField(null=True, blank=True)
    correlation_id = models.UUIDField(null=True, blank=True)
    tenant_id = models.CharField(max_length=100, blank=True, db_index=True)
    region = models.CharField(max_length=50, default='us-east-1')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['aggregate_type', 'aggregate_id', 'version']),
            models.Index(fields=['event_name', 'timestamp']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['tenant_id', 'timestamp']),
            models.Index(fields=['processed', 'error_count']),
        ]
        verbose_name = 'Event Store'
        verbose_name_plural = 'Event Stores'

    def __str__(self):
        return f"{self.event_name} ({self.aggregate_type}:{self.aggregate_id})"


class EventProjection(models.Model):
    """Read model projections from event stream"""
    projection_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    projection_name = models.CharField(max_length=200, db_index=True)
    aggregate_type = models.CharField(max_length=100, db_index=True)
    aggregate_id = models.CharField(max_length=100, db_index=True)
    state = models.JSONField(default=dict)
    version = models.PositiveIntegerField(default=0)
    is_stale = models.BooleanField(default=False)
    last_event_timestamp = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['projection_name', 'aggregate_type', 'aggregate_id']
        indexes = [
            models.Index(fields=['projection_name', 'is_stale']),
            models.Index(fields=['aggregate_type', 'aggregate_id']),
        ]
        verbose_name = 'Event Projection'

    def __str__(self):
        return f"{self.projection_name} - {self.aggregate_type}:{self.aggregate_id}"


class EventHandler(models.Model):
    """Event handler registry and status"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('failed', 'Failed'),
        ('disabled', 'Disabled'),
    ]

    handler_id = models.CharField(max_length=200, primary_key=True)
    handler_name = models.CharField(max_length=255)
    event_names = models.JSONField(default=list)
    handler_type = models.CharField(max_length=50, default='sync', choices=[
        ('sync', 'Synchronous'),
        ('async', 'Asynchronous'),
        ('scheduled', 'Scheduled'),
    ])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    retry_policy = models.JSONField(default=dict, blank=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)
    processed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    avg_processing_time_ms = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['handler_name']
        verbose_name = 'Event Handler'

    def __str__(self):
        return self.handler_name


class EventSubscription(models.Model):
    """External event subscriptions (webhooks, SQS, etc.)"""
    SUBSCRIPTION_TYPES = [
        ('webhook', 'Webhook'),
        ('sqs', 'AWS SQS'),
        ('sns', 'AWS SNS'),
        ('kafka', 'Kafka Topic'),
        ('redis', 'Redis Pub/Sub'),
    ]

    subscription_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    endpoint = models.CharField(max_length=500)
    event_filter = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveIntegerField(default=3)
    timeout_seconds = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    last_delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Event Subscription'

    def __str__(self):
        return f"{self.name} ({self.subscription_type})"


class SagaInstance(models.Model):
    """Distributed saga orchestration"""
    SAGA_STATES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('compensating', 'Compensating'),
        ('compensated', 'Compensated'),
        ('failed', 'Failed'),
    ]

    saga_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    saga_type = models.CharField(max_length=100, db_index=True)
    correlation_id = models.UUIDField(db_index=True)
    state = models.CharField(max_length=20, choices=SAGA_STATES, default='pending')
    current_step = models.PositiveIntegerField(default=0)
    total_steps = models.PositiveIntegerField(default=0)
    context = models.JSONField(default=dict, blank=True)
    steps_log = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['saga_type', 'state']),
            models.Index(fields=['correlation_id']),
        ]
        verbose_name = 'Saga Instance'

    def __str__(self):
        return f"{self.saga_type} ({self.state})"


class DeadLetterQueue(models.Model):
    """Failed events for manual inspection and replay"""
    dlq_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    original_event = models.ForeignKey(EventStore, on_delete=models.SET_NULL, null=True, related_name='dlq_entries')
    error_message = models.TextField()
    error_stack = models.TextField(blank=True)
    handler_id = models.CharField(max_length=200, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dead Letter Queue'
        verbose_name_plural = 'Dead Letter Queues'

    def __str__(self):
        return f"DLQ: {self.original_event}"
