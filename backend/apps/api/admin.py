
from django.contrib import admin
from .models import APIKey, Webhook, APILog

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'key_prefix', 'rate_limit', 'is_active', 'last_used_at']
    list_filter = ['is_active']

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'retry_count']

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'status_code', 'duration_ms', 'created_at']
    list_filter = ['status_code', 'method']
