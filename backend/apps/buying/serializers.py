from rest_framework import serializers
from apps.core.workflow import validate_transition, run_side_effect
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseTaxCharge, PurchasePayment

PO_TRANSITIONS = {
    'Draft': {'Submitted', 'Cancelled'},
    'Submitted': {'Received', 'Cancelled'},
    'Received': set(),
    'Cancelled': set(),
}

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

    def validate(self, data):
        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(PO_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == 'Received':
            run_side_effect(instance.receive_stock)
        return instance
