from django.apps import AppConfig

class SellingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.selling'

    def ready(self):
        import apps.selling.signals  # noqa: F401
