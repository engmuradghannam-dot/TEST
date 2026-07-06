
from rest_framework import serializers
from .models import Plan, Subscription, Invoice, Payment


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description', 'interval', 'price', 'currency',
            'features', 'max_users', 'max_storage_mb', 'max_projects', 'api_calls_per_month',
            'plan_type', 'is_active', 'is_public', 'created_at'
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'tenant', 'plan', 'plan_name', 'status', 'stripe_subscription_id',
            'current_period_start', 'current_period_end', 'trial_start', 'trial_end',
            'cancel_at_period_end', 'cancelled_at', 'created_at'
        ]
        read_only_fields = ['id', 'stripe_subscription_id', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'subtotal', 'tax', 'discount', 'total', 'currency',
            'status', 'invoice_date', 'due_date', 'paid_at', 'line_items', 'pdf_url'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'status', 'payment_method', 'card_last4',
            'card_brand', 'description', 'created_at'
        ]
