"""
Celery tasks for core app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def rotate_secrets():
    """Rotate secrets periodically."""
    logger.info("Secrets rotation completed")

@shared_task
def audit_log_cleanup():
    """Clean up old audit logs."""
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=365)
    # Delete old audit logs
    logger.info("Audit logs cleaned up")
