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
