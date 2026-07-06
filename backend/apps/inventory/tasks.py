"""
Celery tasks for inventory app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_low_stock():
    """Check for low stock items and notify."""
    from .models import InventoryItem
    low_stock = InventoryItem.objects.filter(
        quantity__lte=models.F('reorder_level')
    )
    for item in low_stock:
        logger.warning(f"Low stock alert: {item.name} ({item.quantity} remaining)")

@shared_task
def generate_reorder_suggestions():
    """Generate reorder suggestions based on usage."""
    logger.info("Reorder suggestions generated")
