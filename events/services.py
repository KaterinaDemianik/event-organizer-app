from __future__ import annotations

from typing import Dict, List, Tuple, Optional

from django.db.models import Q
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


class RSVPService:
    """Сервіс для роботи з RSVP (реєстрацією на події)"""

    @staticmethod
    def get_conflicting_events(user, event: Event) -> List[Event]:
        """
        Повертає список подій, на які користувач вже зареєстрований
        і які перетинаються в часі з вказаною подією.
        
        Конфлікт часу: події перетинаються, якщо:
        - event.starts_at < other.ends_at AND event.ends_at > other.starts_at
        """
        from tickets.models import RSVP
        
        user_rsvp_event_ids = RSVP.objects.filter(
            user=user,
            status="going"
        ).values_list("event_id", flat=True)
        
        if not user_rsvp_event_ids:
            return []
        
        conflicting = Event.objects.filter(
            id__in=user_rsvp_event_ids
        ).filter(
            starts_at__lt=event.ends_at,
            ends_at__gt=event.starts_at
        ).exclude(
            id=event.id
        )
        
        return list(conflicting)

    @staticmethod
    def check_time_conflict(user, event: Event) -> Tuple[bool, Optional[Event]]:
        """
        Перевіряє чи є конфлікт часу для RSVP.
        
        Returns:
            Tuple (has_conflict, conflicting_event)
            - has_conflict: True якщо є конфлікт
            - conflicting_event: перша подія з конфліктом (або None)
        """
        conflicts = RSVPService.get_conflicting_events(user, event)
        if conflicts:
            return True, conflicts[0]
        return False, None

    @staticmethod
    def can_create_rsvp(user, event: Event) -> Tuple[bool, Optional[str]]:
        """
        Комплексна перевірка чи можна створити RSVP.
        
        Returns:
            Tuple (can_create, error_message)
        """
        from tickets.models import RSVP
        
        # Перевірка статусу події
        if event.status == Event.DRAFT:
            return False, "Реєстрація недоступна: подія ще не опублікована"
        
        if event.status == Event.CANCELLED:
            return False, "Реєстрація недоступна: подію скасовано"
        
        if event.status == Event.ARCHIVED:
            return False, "Реєстрація недоступна: подія архівована"
        
        # Перевірка чи подія вже розпочалась
        if event.starts_at <= timezone.now():
            return False, "Реєстрація недоступна: подія вже розпочалась"
        
        if RSVP.objects.filter(user=user, event=event).exists():
            return False, "Ви вже зареєстровані на цю подію"
        
        if event.capacity is not None:
            current = RSVP.objects.filter(event=event, status="going").count()
            if current >= event.capacity:
                return False, "Реєстрація недоступна: всі місця зайняті"
        
        has_conflict, conflicting_event = RSVPService.check_time_conflict(user, event)
        if has_conflict:
            return False, f"Конфлікт часу: ви вже зареєстровані на подію \"{conflicting_event.title}\", яка перетинається в часі"
        
        return True, None