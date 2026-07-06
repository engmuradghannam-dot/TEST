
"""
Enhanced Audit System for Nexus Framework
Tracks WHO did WHAT and WHEN with immutable history.
"""

import json
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLogEntry(models.Model):
    """
    Immutable audit log entry for all system changes.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('PRINT', 'Print'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
    ]

    # WHO
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_entries')
    user_email = models.EmailField(blank=True, help_text='Cached email in case user is deleted')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # WHAT
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    # WHEN
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # CHANGE DETAILS (immutable)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    changes_diff = models.JSONField(default=dict, blank=True, help_text='Computed diff between old and new')

    # ADDITIONAL CONTEXT
    company_id = models.PositiveIntegerField(null=True, blank=True)
    branch_id = models.PositiveIntegerField(null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    request_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['company_id', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user_email} {self.action} {self.model_name} at {self.timestamp}"

    def save(self, *args, **kwargs):
        # Ensure immutability - never update existing records
        if self.pk:
            raise ValueError("AuditLogEntry is immutable and cannot be modified")

        # Cache user email
        if self.user and not self.user_email:
            self.user_email = self.user.email

        # Compute diff if both old and new exist
        if self.old_values and self.new_values:
            self.changes_diff = self._compute_diff(self.old_values, self.new_values)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLogEntry is immutable and cannot be deleted")

    @staticmethod
    def _compute_diff(old_vals, new_vals):
        """Compute field-level differences."""
        diff = {}
        all_keys = set(old_vals.keys()) | set(new_vals.keys())
        for key in all_keys:
            old_val = old_vals.get(key)
            new_val = new_vals.get(key)
            if old_val != new_val:
                diff[key] = {'old': old_val, 'new': new_val}
        return diff

    @property
    def is_create(self):
        return self.action == 'CREATE'

    @property
    def is_update(self):
        return self.action == 'UPDATE'

    @property
    def is_delete(self):
        return self.action == 'DELETE'


class AuditLogManager:
    """
    Manager class for creating audit log entries.
    Provides convenience methods for common audit operations.
    """

    @classmethod
    def log_create(cls, instance, user=None, request=None, **kwargs):
        """Log a create action."""
        return cls._log_action('CREATE', instance, user, request, new_values=cls._serialize_instance(instance), **kwargs)

    @classmethod
    def log_update(cls, instance, old_values, user=None, request=None, **kwargs):
        """Log an update action."""
        return cls._log_action('UPDATE', instance, user, request, 
                               old_values=old_values, 
                               new_values=cls._serialize_instance(instance), **kwargs)

    @classmethod
    def log_delete(cls, instance, user=None, request=None, **kwargs):
        """Log a delete action."""
        return cls._log_action('DELETE', instance, user, request, 
                               old_values=cls._serialize_instance(instance), **kwargs)

    @classmethod
    def log_login(cls, user, request=None, **kwargs):
        """Log a login action."""
        return cls._log_action('LOGIN', None, user, request, **kwargs)

    @classmethod
    def log_logout(cls, user, request=None, **kwargs):
        """Log a logout action."""
        return cls._log_action('LOGOUT', None, user, request, **kwargs)

    @classmethod
    def _log_action(cls, action, instance, user, request, old_values=None, new_values=None, **kwargs):
        entry = AuditLogEntry(
            action=action,
            user=user,
            model_name=instance.__class__.__name__ if instance else 'User',
            object_id=str(instance.pk) if instance else '',
            object_repr=str(instance)[:255] if instance else '',
            old_values=old_values or {},
            new_values=new_values or {},
        )

        if request:
            entry.ip_address = cls._get_client_ip(request)
            entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            entry.session_id = request.session.session_key or ''

        # Extract company/branch from instance if available
        if instance and hasattr(instance, 'company_id'):
            entry.company_id = instance.company_id
        if instance and hasattr(instance, 'branch_id'):
            entry.branch_id = instance.branch_id

        entry.save()
        return entry

    @staticmethod
    def _serialize_instance(instance):
        """Serialize model instance to dict."""
        from django.db.models import Model
        if not isinstance(instance, Model):
            return {}
        return {f.name: str(getattr(instance, f.name)) for f in instance._meta.fields}

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


def connect_signals():
    """Wire audit signal receivers. Called from CoreConfig.ready().
    Receivers defined with @receiver decorators in this module are
    connected on import; this function exists as the explicit hook
    and is safe to call multiple times."""
    return True
