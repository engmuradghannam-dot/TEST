
from rest_framework import serializers
from .models import Plugin, TenantPlugin, PluginHook, PluginReview


class PluginSerializer(serializers.ModelSerializer):
    """Serializer for Plugin model."""
    class Meta:
        model = Plugin
        fields = [
            'id', 'name', 'slug', 'description', 'version', 'author',
            'status', 'is_published', 'is_premium', 'price', 'category',
            'tags', 'icon', 'download_count', 'rating', 'review_count',
            'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'download_count', 'rating', 'review_count', 'created_at']


class TenantPluginSerializer(serializers.ModelSerializer):
    """Serializer for TenantPlugin model."""
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    plugin_slug = serializers.CharField(source='plugin.slug', read_only=True)
    plugin_version = serializers.CharField(source='plugin.version', read_only=True)

    class Meta:
        model = TenantPlugin
        fields = [
            'id', 'tenant', 'plugin', 'plugin_name', 'plugin_slug', 'plugin_version',
            'status', 'config', 'is_paid', 'paid_until', 'installed_at'
        ]
        read_only_fields = ['id', 'installed_at']


class PluginHookSerializer(serializers.ModelSerializer):
    """Serializer for PluginHook model."""
    class Meta:
        model = PluginHook
        fields = ['id', 'plugin', 'name', 'event', 'hook_type', 'priority', 'is_active']
        read_only_fields = ['id']


class PluginReviewSerializer(serializers.ModelSerializer):
    """Serializer for PluginReview model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = PluginReview
        fields = ['id', 'plugin', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']
