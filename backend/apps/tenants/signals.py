
"""
Signals for tenant lifecycle management.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_tenants.utils import schema_context
from .models import Tenant, TenantSettings, TenantMembership


@receiver(post_save, sender=Tenant)
def create_tenant_settings(sender, instance, created, **kwargs):
    """Create default settings when a new tenant is created."""
    if created:
        TenantSettings.objects.create(tenant=instance)


@receiver(post_save, sender=Tenant)
def seed_tenant_data(sender, instance, created, **kwargs):
    """Seed initial data when tenant schema is created."""
    if created and instance.auto_create_schema:
        # Seed data will be handled by a Celery task
        from celery import current_app
        current_app.send_task('apps.tenants.tasks.seed_tenant', args=[instance.id])


@receiver(post_save, sender=TenantMembership)
def handle_membership_change(sender, instance, created, **kwargs):
    """Handle membership changes - send notifications, update counts."""
    if created:
        # Update tenant user count
        tenant = instance.tenant
        current_count = tenant.memberships.filter(is_active=True).count()
        if current_count > tenant.max_users:
            # Log warning or send notification
            pass
