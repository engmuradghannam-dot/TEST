"""
Staging settings for Nexus SaaS.
"""
from .settings import *

DEBUG = False

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING['handlers']['console']['formatter'] = 'json'
LOGGING['handlers']['file']['formatter'] = 'json'

# Celery
CELERY_TASK_ALWAYS_EAGER = False

# Sentry
SENTRY_ENVIRONMENT = 'staging'

# Stripe - test mode
STRIPE_LIVE_MODE = False
