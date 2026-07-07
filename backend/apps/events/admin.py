from django.contrib import admin
from .models import (
    EventStore, EventProjection, EventHandler,
    EventSubscription, SagaInstance, DeadLetterQueue
)

@admin.register(EventStore)
class EventStoreAdmin(admin.ModelAdmin):
    list_display = ['event_name', 'aggregate_type', 'aggregate_id', 'version', 'processed', 'timestamp']
    list_filter = ['event_type', 'processed', 'region', 'tenant_id']
    search_fields = ['event_name', 'aggregate_type', 'aggregate_id']
    readonly_fields = ['event_id', 'timestamp', 'processed_at']
    date_hierarchy = 'timestamp'

@admin.register(EventProjection)
class EventProjectionAdmin(admin.ModelAdmin):
    list_display = ['projection_name', 'aggregate_type', 'aggregate_id', 'version', 'is_stale', 'updated_at']
    list_filter = ['projection_name', 'is_stale']
    search_fields = ['projection_name', 'aggregate_id']

@admin.register(EventHandler)
class EventHandlerAdmin(admin.ModelAdmin):
    list_display = ['handler_name', 'handler_type', 'status', 'processed_count', 'failed_count', 'last_processed_at']
    list_filter = ['status', 'handler_type', 'is_active']
    search_fields = ['handler_name', 'handler_id']

@admin.register(EventSubscription)
class EventSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'subscription_type', 'endpoint', 'is_active', 'delivery_count', 'last_delivered_at']
    list_filter = ['subscription_type', 'is_active']

@admin.register(SagaInstance)
class SagaInstanceAdmin(admin.ModelAdmin):
    list_display = ['saga_type', 'state', 'current_step', 'total_steps', 'started_at', 'completed_at']
    list_filter = ['saga_type', 'state']
    date_hierarchy = 'started_at'

@admin.register(DeadLetterQueue)
class DeadLetterQueueAdmin(admin.ModelAdmin):
    list_display = ['dlq_id', 'handler_id', 'retry_count', 'resolved', 'created_at']
    list_filter = ['resolved', 'handler_id']
    actions = ['mark_resolved', 'retry_events']

    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True, resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected as resolved"

    def retry_events(self, request, queryset):
        for entry in queryset.filter(resolved=False):
            if entry.original_event:
                entry.original_event.processed = False
                entry.original_event.save()
    retry_events.short_description = "Retry selected events"
