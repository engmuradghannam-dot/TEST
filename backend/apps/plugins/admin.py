
from django.contrib import admin
from .models import Plugin, TenantPlugin, PluginHook, PluginReview


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'status', 'is_published', 'is_premium', 'price', 'download_count', 'rating']
    list_filter = ['status', 'is_published', 'is_premium', 'is_verified', 'category']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['download_count', 'rating', 'review_count', 'created_at', 'updated_at']


@admin.register(TenantPlugin)
class TenantPluginAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plugin', 'status', 'is_paid', 'installed_at']
    list_filter = ['status', 'is_paid', 'installed_at']
    search_fields = ['tenant__name', 'plugin__name']


@admin.register(PluginHook)
class PluginHookAdmin(admin.ModelAdmin):
    list_display = ['plugin', 'name', 'event', 'hook_type', 'priority', 'is_active']
    list_filter = ['hook_type', 'is_active']
    search_fields = ['name', 'event', 'plugin__name']


@admin.register(PluginReview)
class PluginReviewAdmin(admin.ModelAdmin):
    list_display = ['plugin', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['plugin__name', 'user__email']
