
from django.contrib import admin
from .models import Plan, Subscription, Invoice, Payment, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'plan_type', 'price', 'interval', 'is_active', 'is_public', 'sort_order']
    list_filter = ['plan_type', 'is_active', 'is_public', 'interval']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['stripe_product_id', 'stripe_price_id']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'current_period_end', 'cancel_at_period_end']
    list_filter = ['status', 'plan', 'cancel_at_period_end']
    search_fields = ['tenant__name', 'stripe_subscription_id']
    readonly_fields = ['stripe_subscription_id', 'stripe_customer_id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'tenant', 'total', 'currency', 'status', 'invoice_date']
    list_filter = ['status', 'currency', 'invoice_date']
    search_fields = ['invoice_number', 'tenant__name', 'stripe_invoice_id']
    readonly_fields = ['stripe_invoice_id', 'stripe_payment_intent_id']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'currency']
    search_fields = ['tenant__name', 'stripe_payment_intent_id', 'stripe_charge_id']


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'usage_type', 'quantity', 'unit', 'billing_period_start']
    list_filter = ['usage_type', 'billing_period_start']
    search_fields = ['tenant__name']
