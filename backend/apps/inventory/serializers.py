from rest_framework import serializers
from .models import (
    Item, ItemGroup, StockEntry, ItemSerialNumber, ItemBatch,
    StockReconciliation, StockReconciliationItem,
)

class ItemGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGroup
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = '__all__'

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
