from rest_framework import serializers
from apps.core.workflow import validate_transition, run_side_effect
from .models import BOM, BOMItem, WorkOrder

WO_TRANSITIONS = {
    'Draft': {'In Progress', 'Cancelled'},
    'In Progress': {'Completed', 'Cancelled'},
    'Completed': set(),
    'Cancelled': set(),
}

class BOMItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMItem
        fields = '__all__'

class BOMSerializer(serializers.ModelSerializer):
    items = BOMItemSerializer(many=True, read_only=True)
    raw_materials_cost = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()
    class Meta:
        model = BOM
        fields = '__all__'

class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'

    def validate(self, data):
        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(WO_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == 'Completed':
            run_side_effect(instance.complete_production)
        return instance
