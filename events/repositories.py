"""
Repository Pattern для абстракції доступу до даних.
Відокремлює бізнес-логіку від деталей роботи з БД.
"""
from typing import List, Optional
from django.db.models import QuerySet, Count, Q
from django.utils import timezone

from .models import Event
from .specifications import Specification, apply_specifications


class EventRepository:
    """
    Репозиторій для роботи з подіями.
    Надає колекціє-подібний інтерфейс для доступу до подій.
    """

    def get_by_id(self, event_id: int) -> Optional[Event]:
        """Отримує подію за ID"""
        try:
            return Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return None

    def get_all(self) -> QuerySet[Event]:
        """Повертає всі події"""
        return Event.objects.all()

    def get_published(self) -> QuerySet[Event]:
        """Повертає тільки опубліковані події"""
        return Event.objects.filter(status=Event.PUBLISHED)

    def get_upcoming(self) -> QuerySet[Event]:
        """Повертає майбутні опубліковані події"""
        now = timezone.now()
        return Event.objects.filter(
            status=Event.PUBLISHED,
            starts_at__gte=now
        ).order_by('starts_at')

    def get_by_organizer(self, user) -> QuerySet[Event]:
        """Повертає події організатора"""
        return Event.objects.filter(organizer=user)

    def find_by_specification(self, *specs: Specification) -> QuerySet[Event]:
        """Фільтрує події за специфікаціями"""
        return apply_specifications(Event.objects.all(), *specs)

    def save(self, event: Event) -> Event:
        """Зберігає подію"""
        event.save()
        return event

    def delete(self, event: Event) -> None:
        """Видаляє подію"""
        event.delete()

    def get_with_rsvp_count(self) -> QuerySet[Event]:
        """Повертає події з анотацією кількості учасників"""
        return Event.objects.annotate(rsvp_count=Count('rsvps'))

    def search(self, query: str) -> QuerySet[Event]:
        """Пошук подій за назвою, описом або локацією"""
        return Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    def get_archived(self) -> QuerySet[Event]:
        """Повертає архівні події"""
        return Event.objects.filter(status=Event.ARCHIVED)

    def count_by_status(self, status: str) -> int:
        """Підраховує кількість подій за статусом"""
        return Event.objects.filter(status=status).count()
