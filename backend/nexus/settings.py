import os

"""
Nexus Framework - Django ERP Settings
Multi-tenant SaaS Architecture with django-tenants
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

_INSECURE_DEFAULT_KEY = 'django-insecure-nexus-dev-key-change-in-production'
SECRET_KEY = os.getenv('SECRET_KEY', _INSECURE_DEFAULT_KEY)
if not DEBUG and SECRET_KEY == _INSECURE_DEFAULT_KEY:
    raise RuntimeError(
        'Refusing to start with DEBUG=False and no SECRET_KEY set. '
        'Set the SECRET_KEY environment variable before deploying to production.'
    )

# ───────────────────────────────────────────
# MULTI-TENANCY CONFIGURATION (django-tenants)
# ───────────────────────────────────────────
SHARED_APPS = [
    'django_tenants',  # Must be first
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'guardian',
    # Public schema apps (shared across all tenants)
    'apps.tenants',
    'apps.plugins',
    'apps.billing',
    'apps.core',
]

TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'guardian',
    # Tenant-specific apps
    'apps.core',
    'apps.accounts',
    'apps.inventory',
    'apps.buying',
    'apps.selling',
    'apps.manufacturing',
    'apps.hr',
    'apps.crm',
    'apps.projects',
    'apps.assets',
    'apps.workflow',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Tenant configuration
TENANT_MODEL = "tenants.Tenant"  # app.Model
TENANT_DOMAIN_MODEL = "tenants.Domain"  # app.Model
PUBLIC_SCHEMA_NAME = os.getenv('PUBLIC_SCHEMA_NAME', 'public')

# ───────────────────────────────────────────
# MIDDLEWARE
# ───────────────────────────────────────────
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'apps.tenants.middleware.NexusTenantMiddleware',
    'apps.tenants.middleware.TenantLimitMiddleware',
    'apps.tenants.middleware.TenantSecurityHeadersMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.CurrentUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ───────────────────────────────────────────
# DATABASE (PostgreSQL with django-tenants)
# ───────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DB_NAME', 'nexus'),
        'USER': os.getenv('DB_USER', 'nexus'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'nexus'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# ───────────────────────────────────────────
# CACHING (Redis)
# ───────────────────────────────────────────
_redis_url_env = os.getenv('REDIS_URL')
if _redis_url_env or not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url_env or 'redis://redis:6379/1',
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
        }
    }
else:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

# ───────────────────────────────────────────
# AUTHENTICATION
# ───────────────────────────────────────────
AUTH_USER_MODEL = 'tenants.TenantUser'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

ANONYMOUS_USER_ID = -1

# ───────────────────────────────────────────
# INTERNATIONALIZATION
# ───────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ───────────────────────────────────────────
# STATIC & MEDIA FILES
# ───────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ───────────────────────────────────────────
# REST FRAMEWORK
# ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '300/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# ───────────────────────────────────────────
# CORS
# ───────────────────────────────────────────
_allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '')
if _allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    raise RuntimeError(
        'Refusing to start with DEBUG=False and no ALLOWED_HOSTS set.'
    )

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    _cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins_env.split(',') if o.strip()]

# ───────────────────────────────────────────
# CELERY
# ───────────────────────────────────────────
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_TASK_ALWAYS_EAGER = not _redis_url_env and DEBUG
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ───────────────────────────────────────────
# EMAIL
# ───────────────────────────────────────────
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@nexus-saas.com')
if DEBUG and not os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', '')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'

# ───────────────────────────────────────────
# STRIPE BILLING
# ───────────────────────────────────────────
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
STRIPE_WEBHOOK_URL = os.getenv('STRIPE_WEBHOOK_URL', '/api/billing/webhook/')

# ───────────────────────────────────────────
# SENTRY
# ───────────────────────────────────────────
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        release=os.getenv('SENTRY_RELEASE', 'unknown'),
        send_default_pii=False,
    )

# ───────────────────────────────────────────
# OPENTELEMETRY (Prometheus + Tempo)
# ───────────────────────────────────────────
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', '')
OTEL_SERVICE_NAME = os.getenv('OTEL_SERVICE_NAME', 'nexus-backend')
OTEL_TRACES_SAMPLER = os.getenv('OTEL_TRACES_SAMPLER', 'parentbased_traceidratio')
OTEL_TRACES_SAMPLER_ARG = os.getenv('OTEL_TRACES_SAMPLER_ARG', '0.1')

# ───────────────────────────────────────────
# SECURITY HARDENING
# ───────────────────────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ───────────────────────────────────────────
# LOGGING (Structured for Loki)
# ───────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d %(funcName)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/nexus.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django_tenants': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ───────────────────────────────────────────
# PLUGIN SYSTEM
# ───────────────────────────────────────────
PLUGIN_DIRECTORY = BASE_DIR / 'plugins'
PLUGIN_AUTO_DISCOVER = True
PLUGIN_HOOK_REGISTRY = 'apps.plugins.models.HookRegistry'

# ───────────────────────────────────────────
# TENANT SETTINGS
# ───────────────────────────────────────────
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True
TENANT_NOT_FOUND_EXCEPTION_CLASS = 'django.http.Http404'

# ───────────────────────────────────────────
# ROOT URLCONF & WSGI
# ───────────────────────────────────────────
ROOT_URLCONF = 'nexus.urls'
WSGI_APPLICATION = 'nexus.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]
