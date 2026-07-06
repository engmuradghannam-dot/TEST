"""
API Models - Webhooks, API Keys, Rate Limits
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class APIKey(models.Model):
    """Developer API Keys"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='api_keys')
    user = models.ForeignKey('tenants.TenantUser', on_delete=models.CASCADE, related_name='api_keys')

    name = models.CharField(max_length=200, verbose_name=_('Key Name'))
    key_hash = models.CharField(max_length=128, verbose_name=_('Key Hash'))
    key_prefix = models.CharField(max_length=16, verbose_name=_('Key Prefix'))

    scopes = models.JSONField(default=list, verbose_name=_('Scopes'))
    rate_limit = models.PositiveIntegerField(default=1000, verbose_name=_('Rate Limit/min'))

    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')


class Webhook(models.Model):
    """Webhook configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='webhooks')

    name = models.CharField(max_length=200, verbose_name=_('Name'))
    url = models.URLField(verbose_name=_('Webhook URL'))
    events = models.JSONField(default=list, verbose_name=_('Events'))
    secret = models.CharField(max_length=255, verbose_name=_('Secret'))

    headers = models.JSONField(default=dict, blank=True, verbose_name=_('Custom Headers'))

    is_active = models.BooleanField(default=True)
    retry_count = models.PositiveIntegerField(default=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Webhook')
        verbose_name_plural = _('Webhooks')


class APILog(models.Model):
    """API request/response logging"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.PositiveIntegerField()

    request_body = models.JSONField(default=dict)
    response_body = models.JSONField(default=dict)

    user_agent = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField()

    duration_ms = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('API Log')
        verbose_name_plural = _('API Logs')
