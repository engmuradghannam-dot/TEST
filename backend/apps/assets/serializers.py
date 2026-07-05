from rest_framework import serializers
from .models import AssetCategory, Asset

class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = '__all__'

class AssetSerializer(serializers.ModelSerializer):
    accumulated_depreciation = serializers.ReadOnlyField()
    book_value = serializers.ReadOnlyField()
    class Meta:
        model = Asset
        fields = '__all__'

    def validate(self, data):
        purchase_value = data.get('purchase_value', getattr(self.instance, 'purchase_value', None))
        salvage_value = data.get('salvage_value', getattr(self.instance, 'salvage_value', None))
        if purchase_value is not None and salvage_value is not None and salvage_value > purchase_value:
            raise serializers.ValidationError("Salvage value cannot exceed the purchase value.")
        return data
