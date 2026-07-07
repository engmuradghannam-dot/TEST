"""Test settings: plain PostgreSQL (no tenant schemas) so the financial
logic suite runs fast and deterministic. Multitenancy has its own
dedicated tests that use the full django-tenants stack."""
from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nexus_test',
        'USER': 'nexus',
        'PASSWORD': 'nexus',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
DATABASE_ROUTERS = []
# strip django-tenants machinery for logic tests
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != 'django_tenants']  # noqa: F405
MIDDLEWARE = [m for m in MIDDLEWARE  # noqa: F405
              if 'tenants' not in m and 'gateway' not in m.lower()]
CELERY_TASK_ALWAYS_EAGER = True
LOGGING = {'version': 1, 'disable_existing_loggers': True}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
