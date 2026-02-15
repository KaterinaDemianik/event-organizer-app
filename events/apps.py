from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        """Підключення сигналів при завантаженні додатку"""
        import events.signals  # noqa: F401