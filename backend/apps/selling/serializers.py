from rest_framework import serializers
from .models import Customer, SalesOrder, SalesOrderItem, SalesTaxCharge, SalesPayment

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
