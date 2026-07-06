"""
Celery tasks for plugins app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_plugin_ratings():
    """Update plugin ratings from reviews."""
    from django.db.models import Avg
    from .models import Plugin, PluginReview

    for plugin in Plugin.objects.all():
        avg = PluginReview.objects.filter(plugin=plugin).aggregate(
            Avg('rating')
        )['rating__avg'] or 0
        plugin.rating = round(avg, 2)
        plugin.review_count = PluginReview.objects.filter(plugin=plugin).count()
        plugin.save()
        logger.info(f"Updated rating for {plugin.name}: {plugin.rating}")
