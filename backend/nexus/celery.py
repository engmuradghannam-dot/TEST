"""
Celery Configuration for Nexus SaaS.
Supports: development, staging, production
"""
import os
from celery import Celery
from celery.signals import task_failure, task_success, task_retry
import logging

logger = logging.getLogger(__name__)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')

app = Celery('nexus')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# ───────────────────────────────────────────
# Task Routing
# ───────────────────────────────────────────
app.conf.task_routes = {
    # High priority - billing, user management
    'apps.billing.*': {'queue': 'billing'},
    'apps.tenants.*': {'queue': 'tenants'},

    # Medium priority - business logic
    'apps.accounts.*': {'queue': 'accounting'},
    'apps.inventory.*': {'queue': 'inventory'},
    'apps.buying.*': {'queue': 'purchasing'},
    'apps.selling.*': {'queue': 'sales'},

    # Low priority - background jobs
    'apps.hr.*': {'queue': 'hr'},
    'apps.crm.*': {'queue': 'crm'},
    'apps.projects.*': {'queue': 'projects'},
    'apps.manufacturing.*': {'queue': 'manufacturing'},

    # Plugin tasks
    'apps.plugins.*': {'queue': 'plugins'},

    # Default queue
    '*': {'queue': 'default'},
}

# ───────────────────────────────────────────
# Task Configuration
# ───────────────────────────────────────────
app.conf.update(
    # Task execution
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task results
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    result_expires=3600,
    result_extended=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 min soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=512000,  # 512MB

    # Acknowledge after task completes (not before)
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,

    # Beat scheduler
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    beat_max_loop_interval=300,
)

# ───────────────────────────────────────────
# Task Signals
# ───────────────────────────────────────────
@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Log successful task completion."""
    logger.info(f"Task {sender.name} completed successfully: {result}")

@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failures and send alerts."""
    logger.error(f"Task {sender.name} failed: {exception}")

    # Send to Sentry if configured
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exception)
    except ImportError:
        pass

@task_retry.connect
def handle_task_retry(sender=None, request=None, reason=None, **kwargs):
    """Log task retries."""
    logger.warning(f"Task {sender.name} retrying: {reason}")

# ───────────────────────────────────────────
# Periodic Tasks (Beat Schedule)
# ───────────────────────────────────────────
app.conf.beat_schedule = {
    # Billing
    'check-expired-subscriptions': {
        'task': 'apps.billing.tasks.check_expired_subscriptions',
        'schedule': 3600.0,  # Every hour
    },
    'generate-monthly-invoices': {
        'task': 'apps.billing.tasks.generate_monthly_invoices',
        'schedule': 86400.0,  # Daily
    },

    # Tenants
    'cleanup-inactive-tenants': {
        'task': 'apps.tenants.tasks.cleanup_inactive_tenants',
        'schedule': 86400.0,  # Daily
    },
    'sync-tenant-usage': {
        'task': 'apps.tenants.tasks.sync_tenant_usage',
        'schedule': 3600.0,  # Every hour
    },

    # Inventory
    'check-low-stock': {
        'task': 'apps.inventory.tasks.check_low_stock',
        'schedule': 3600.0,  # Every hour
    },
    'generate-reorder-suggestions': {
        'task': 'apps.inventory.tasks.generate_reorder_suggestions',
        'schedule': 86400.0,  # Daily
    },

    # HR
    'process-payroll': {
        'task': 'apps.hr.tasks.process_payroll',
        'schedule': 604800.0,  # Weekly
    },
    'check-leave-balances': {
        'task': 'apps.hr.tasks.check_leave_balances',
        'schedule': 86400.0,  # Daily
    },

    # Security
    'rotate-secrets': {
        'task': 'apps.core.tasks.rotate_secrets',
        'schedule': 2592000.0,  # Monthly
    },
    'audit-log-cleanup': {
        'task': 'apps.core.tasks.audit_log_cleanup',
        'schedule': 604800.0,  # Weekly
    },

    # Plugins
    'update-plugin-ratings': {
        'task': 'apps.plugins.tasks.update_plugin_ratings',
        'schedule': 3600.0,  # Every hour
    },
}

# ───────────────────────────────────────────
# Health Check
# ───────────────────────────────────────────
@app.task(bind=True)
def health_check(self):
    """Celery health check task."""
    return {'status': 'ok', 'worker': self.request.hostname}
