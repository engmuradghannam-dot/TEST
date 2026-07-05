from django.apps import AppConfig

class BuyingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.buying'

    def ready(self):
        import apps.buying.signals  # noqa: F401
