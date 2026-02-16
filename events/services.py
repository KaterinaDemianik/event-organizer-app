from __future__ import annotations

from typing import Dict

from django.utils import timezone

from .models import Event


class SingletonMeta(type):
    """Простий Singleton метаклас"""

    _instances: Dict[type, "SingletonMeta"] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class EventArchiveService(metaclass=SingletonMeta):
    """Сервіс для архівування подій"""

    def archive_past_events(self) -> int:
        """Переводить завершені опубліковані події в архів"""

        now = timezone.now()
        queryset = Event.objects.filter(
            status=Event.PUBLISHED,
            ends_at__lt=now,
        )
        count = queryset.count()
        if count:
            queryset.update(status=Event.ARCHIVED)
        return count

    def archive_event(self, event: Event) -> tuple[bool, str | None]:
        """
        Архівує окрему подію з валідацією через State Pattern
        
        Returns:
            Tuple (success, error_message)
        """
        from .states import EventStateManager
        
        is_valid, error_message = EventStateManager.validate_transition(event, Event.ARCHIVED)
        if not is_valid:
            return False, error_message
        
        event.status = Event.ARCHIVED
        event.save(update_fields=["status"])
        return True, None