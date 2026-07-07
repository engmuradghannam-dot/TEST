from django.apps import AppConfig

class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.events'
    verbose_name = 'Event Architecture'

    def ready(self):
        # Import event handlers to register them
        from . import consumers
