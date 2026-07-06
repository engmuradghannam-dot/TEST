from rest_framework import serializers
from apps.core.workflow import validate_transition, run_side_effect
from .models import (
    Item, ItemGroup, StockEntry, ItemSerialNumber, ItemBatch,
    StockReconciliation, StockReconciliationItem,
)

SR_TRANSITIONS = {
    'Draft': {'Submitted', 'Cancelled'},
    'Submitted': set(),
    'Cancelled': set(),
}

class ItemGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGroup
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    stock_quantity = serializers.ReadOnlyField()
    class Meta:
        model = Item
        fields = '__all__'

class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = '__all__'

    def validate(self, data):
        entry_type = data.get('entry_type', getattr(self.instance, 'entry_type', None))
        item = data.get('item', getattr(self.instance, 'item', None))
        quantity = data.get('quantity', getattr(self.instance, 'quantity', None))
        if entry_type == 'Issue' and item and quantity:
            available = item.stock_quantity
            if self.instance and self.instance.entry_type == 'Issue':
                # editing an existing Issue: the quantity it already consumed
                # is still "available" from the item's point of view
                available += self.instance.quantity
            if available < quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock for {item.item_code}: available {available}, requested {quantity}."
                )
        return data

class ItemSerialNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSerialNumber
        fields = '__all__'

class ItemBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBatch
        fields = '__all__'

class StockReconciliationItemSerializer(serializers.ModelSerializer):
    difference = serializers.ReadOnlyField()
    total_difference_value = serializers.ReadOnlyField()
    class Meta:
        model = StockReconciliationItem
        fields = '__all__'

class StockReconciliationSerializer(serializers.ModelSerializer):
    total_difference_value = serializers.ReadOnlyField()
    class Meta:
        model = StockReconciliation
        fields = '__all__'

    def validate(self, data):
        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(SR_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == 'Submitted':
            run_side_effect(instance.apply_adjustments)
        return instance
