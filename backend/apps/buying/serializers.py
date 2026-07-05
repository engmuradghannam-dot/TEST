from rest_framework import serializers
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseTaxCharge, PurchasePayment

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

class PurchaseTaxChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseTaxCharge
        fields = '__all__'

class PurchasePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasePayment
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    total_tax = serializers.ReadOnlyField()
    total_paid = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
