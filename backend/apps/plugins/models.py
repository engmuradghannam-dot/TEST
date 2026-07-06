
"""
Plugin System with marketplace, dynamic loading, and hooks.
"""
import os
import importlib
import logging
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid

logger = logging.getLogger(__name__)


class Plugin(models.Model):
    """
    Plugin model for marketplace and dynamic loading.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Plugin metadata
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    version = models.CharField(max_length=20, default='1.0.0', verbose_name=_('Version'))
    author = models.CharField(max_length=200, blank=True, verbose_name=_('Author'))
    author_email = models.EmailField(blank=True, verbose_name=_('Author Email'))

    # Plugin path/module
    module_path = models.CharField(max_length=500, verbose_name=_('Module Path'))
    entry_point = models.CharField(max_length=200, default='plugin', verbose_name=_('Entry Point'))

    # Status
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PENDING = 'pending', _('Pending Review')
        REJECTED = 'rejected', _('Rejected')
        DEPRECATED = 'deprecated', _('Deprecated')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status')
    )

    # Marketplace
    is_published = models.BooleanField(default=False, verbose_name=_('Is Published'))
    is_premium = models.BooleanField(default=False, verbose_name=_('Is Premium'))
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Price')
    )
    category = models.CharField(max_length=100, blank=True, verbose_name=_('Category'))
    tags = models.JSONField(default=list, blank=True, verbose_name=_('Tags'))
    icon = models.URLField(blank=True, verbose_name=_('Icon'))
    screenshots = models.JSONField(default=list, blank=True, verbose_name=_('Screenshots'))

    # Stats
    download_count = models.PositiveIntegerField(default=0, verbose_name=_('Download Count'))
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name=_('Rating'))
    review_count = models.PositiveIntegerField(default=0, verbose_name=_('Review Count'))

    # Security
    is_verified = models.BooleanField(default=False, verbose_name=_('Is Verified'))
    permissions_required = models.JSONField(default=list, blank=True, verbose_name=_('Permissions Required'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Plugin')
        verbose_name_plural = _('Plugins')

    def __str__(self):
        return f"{self.name} v{self.version}"

    def clean(self):
        if self.status == self.Status.ACTIVE and not self.is_verified:
            raise ValidationError(_('Plugin must be verified before activation.'))

    def load_module(self):
        """Dynamically load the plugin module."""
        try:
            module = importlib.import_module(self.module_path)
            plugin_class = getattr(module, self.entry_point)
            return plugin_class()
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load plugin {self.name}: {e}")
            return None

    def get_hooks(self):
        """Get all hooks registered by this plugin."""
        return PluginHook.objects.filter(plugin=self)


class TenantPlugin(models.Model):
    """
    Many-to-many relationship between tenants and plugins.
    Tracks which plugins are installed/activated per tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='plugins',
        verbose_name=_('Tenant')
    )
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='tenant_installations',
        verbose_name=_('Plugin')
    )

    # Installation status
    class InstallStatus(models.TextChoices):
        INSTALLED = 'installed', _('Installed')
        ACTIVE = 'active', _('Active')
        PAUSED = 'paused', _('Paused')
        UNINSTALLED = 'uninstalled', _('Uninstalled')

    status = models.CharField(
        max_length=20,
        choices=InstallStatus.choices,
        default=InstallStatus.INSTALLED,
        verbose_name=_('Status')
    )

    # Configuration
    config = models.JSONField(default=dict, blank=True, verbose_name=_('Configuration'))

    # Billing
    is_paid = models.BooleanField(default=False, verbose_name=_('Is Paid'))
    paid_until = models.DateField(null=True, blank=True, verbose_name=_('Paid Until'))

    installed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Installed At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        unique_together = ['tenant', 'plugin']
        ordering = ['-installed_at']
        verbose_name = _('Tenant Plugin')
        verbose_name_plural = _('Tenant Plugins')

    def __str__(self):
        return f"{self.plugin.name} @ {self.tenant.name}"

    def is_active(self):
        return self.status == self.InstallStatus.ACTIVE


class PluginHook(models.Model):
    """
    Hook system for plugin extensibility.
    Plugins can register hooks that other plugins can listen to.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='hooks',
        verbose_name=_('Plugin')
    )

    # Hook details
    name = models.CharField(max_length=200, verbose_name=_('Hook Name'))
    event = models.CharField(max_length=200, verbose_name=_('Event'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    # Hook type
    class HookType(models.TextChoices):
        ACTION = 'action', _('Action')
        FILTER = 'filter', _('Filter')
        EVENT = 'event', _('Event')

    hook_type = models.CharField(
        max_length=20,
        choices=HookType.choices,
        default=HookType.ACTION,
        verbose_name=_('Hook Type')
    )

    # Handler
    handler_path = models.CharField(max_length=500, verbose_name=_('Handler Path'))
    priority = models.PositiveIntegerField(default=10, verbose_name=_('Priority'))

    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        ordering = ['priority', '-created_at']
        verbose_name = _('Plugin Hook')
        verbose_name_plural = _('Plugin Hooks')

    def __str__(self):
        return f"{self.plugin.name}:{self.name}"


class HookRegistry:
    """
    Global hook registry for managing plugin hooks at runtime.
    """
    _hooks = {}

    @classmethod
    def register(cls, event, handler, priority=10):
        """Register a hook handler."""
        if event not in cls._hooks:
            cls._hooks[event] = []
        cls._hooks[event].append({
            'handler': handler,
            'priority': priority
        })
        cls._hooks[event].sort(key=lambda x: x['priority'])

    @classmethod
    def unregister(cls, event, handler):
        """Unregister a hook handler."""
        if event in cls._hooks:
            cls._hooks[event] = [
                h for h in cls._hooks[event] 
                if h['handler'] != handler
            ]

    @classmethod
    def trigger(cls, event, *args, **kwargs):
        """Trigger all handlers for an event."""
        results = []
        if event in cls._hooks:
            for hook in cls._hooks[event]:
                try:
                    result = hook['handler'](*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hook handler error for {event}: {e}")
        return results

    @classmethod
    def apply_filters(cls, event, value, *args, **kwargs):
        """Apply filter hooks to a value."""
        if event in cls._hooks:
            for hook in cls._hooks[event]:
                try:
                    value = hook['handler'](value, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Filter hook error for {event}: {e}")
        return value


class PluginReview(models.Model):
    """Reviews for marketplace plugins."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Plugin')
    )
    user = models.ForeignKey(
        'tenants.TenantUser',
        on_delete=models.CASCADE,
        related_name='plugin_reviews',
        verbose_name=_('User')
    )
    rating = models.PositiveIntegerField(verbose_name=_('Rating'))
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        unique_together = ['plugin', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} -> {self.plugin.name} ({self.rating}/5)"
