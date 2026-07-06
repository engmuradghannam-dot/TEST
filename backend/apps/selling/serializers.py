from rest_framework import serializers
from apps.core.workflow import validate_transition, run_side_effect
from .models import Customer, SalesOrder, SalesOrderItem, SalesTaxCharge, SalesPayment

SO_TRANSITIONS = {
    'Draft': {'Submitted', 'Cancelled'},
    'Submitted': {'Delivered', 'Cancelled'},
    'Delivered': set(),
    'Cancelled': set(),
}

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = '__all__'

class SalesTaxChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTaxCharge
        fields = '__all__'

class SalesPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesPayment
        fields = '__all__'

class SalesOrderSerializer(serializers.ModelSerializer):
    total_tax = serializers.ReadOnlyField()
    total_paid = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()
    class Meta:
        model = SalesOrder
        fields = '__all__'

    def validate(self, data):
        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(SO_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == 'Delivered':
            run_side_effect(instance.deliver_stock)
        return instance
