from rest_framework import serializers
from .models import (
    EventStore, EventProjection, EventHandler,
    EventSubscription, SagaInstance, DeadLetterQueue
)

class EventStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStore
        fields = '__all__'
        read_only_fields = ['event_id', 'timestamp', 'processed_at']

class EventStoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStore
        fields = ['event_type', 'aggregate_type', 'aggregate_id', 'event_name', 
                  'payload', 'metadata', 'causation_id', 'correlation_id', 'tenant_id']

class EventProjectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventProjection
        fields = '__all__'

class EventHandlerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventHandler
        fields = '__all__'

class EventSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSubscription
        fields = '__all__'

class SagaInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SagaInstance
        fields = '__all__'
        read_only_fields = ['saga_id', 'started_at', 'completed_at']

class DeadLetterQueueSerializer(serializers.ModelSerializer):
    original_event_details = EventStoreSerializer(source='original_event', read_only=True)

    class Meta:
        model = DeadLetterQueue
        fields = '__all__'
        read_only_fields = ['dlq_id', 'created_at', 'resolved_at']
