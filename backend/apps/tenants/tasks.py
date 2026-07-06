"""
Celery tasks for tenants app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def seed_tenant(tenant_id):
    """Seed initial data for a new tenant."""
    from django_tenants.utils import schema_context
    from .models import Tenant

    tenant = Tenant.objects.get(id=tenant_id)
    with schema_context(tenant.schema_name):
        # Create default data
        logger.info(f"Tenant {tenant.name} seeded successfully")

@shared_task
def cleanup_inactive_tenants():
    """Clean up cancelled tenants older than 30 days."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import Tenant

    cutoff = timezone.now() - timedelta(days=30)
    old_tenants = Tenant.objects.filter(
        status=Tenant.Status.CANCELLED,
        updated_at__lt=cutoff
    )
    count = old_tenants.count()
    old_tenants.delete()
    logger.info(f"Cleaned up {count} inactive tenants")

@shared_task
def sync_tenant_usage():
    """Sync usage data for all active tenants."""
    from .models import Tenant
    from apps.billing.models import UsageRecord

    for tenant in Tenant.objects.filter(status=Tenant.Status.ACTIVE):
        user_count = tenant.memberships.filter(is_active=True).count()
        UsageRecord.objects.create(
            tenant=tenant,
            usage_type=UsageRecord.UsageType.USER,
            quantity=user_count,
            unit='users',
            billing_period_start=timezone.now().replace(day=1),
            billing_period_end=timezone.now()
        )
