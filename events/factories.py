"""
Factory Pattern для створення подій різних типів.
Інкапсулює логіку створення об'єктів.
"""
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from .models import Event


class EventFactory:
    """
    Фабрика для створення подій.
    Спрощує створення подій з різними налаштуваннями.
    """

    @staticmethod
    def create_draft(
        title: str,
        organizer,
        description: str = "",
        location: str = "",
        **kwargs
    ) -> Event:
        """Створює чернетку події"""
        return Event.objects.create(
            title=title,
            organizer=organizer,
            description=description,
            location=location,
            status=Event.DRAFT,
            **kwargs
        )

    @staticmethod
    def create_published(
        title: str,
        organizer,
        starts_at: datetime,
        ends_at: datetime,
        location: str,
        description: str = "",
        capacity: Optional[int] = None,
        **kwargs
    ) -> Event:
        """Створює опубліковану подію"""
        return Event.objects.create(
            title=title,
            organizer=organizer,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            description=description,
            capacity=capacity,
            status=Event.PUBLISHED,
            **kwargs
        )

    @staticmethod
    def create_conference(
        title: str,
        organizer,
        starts_at: datetime,
        duration_days: int = 1,
        location: str = "",
        capacity: Optional[int] = None,
        **kwargs
    ) -> Event:
        """Створює конференцію (багатоденна подія)"""
        ends_at = starts_at + timedelta(days=duration_days)
        return Event.objects.create(
            title=title,
            organizer=organizer,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            capacity=capacity,
            category="Конференція",
            status=Event.PUBLISHED,
            **kwargs
        )

    @staticmethod
    def create_workshop(
        title: str,
        organizer,
        starts_at: datetime,
        duration_hours: int = 2,
        location: str = "",
        capacity: int = 20,
        **kwargs
    ) -> Event:
        """Створює майстер-клас (коротка подія з обмеженою кількістю місць)"""
        ends_at = starts_at + timedelta(hours=duration_hours)
        return Event.objects.create(
            title=title,
            organizer=organizer,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            capacity=capacity,
            category="Майстер-клас",
            status=Event.PUBLISHED,
            **kwargs
        )

    @staticmethod
    def create_meetup(
        title: str,
        organizer,
        starts_at: datetime,
        location: str = "",
        **kwargs
    ) -> Event:
        """Створює зустріч (неформальна подія без обмеження місць)"""
        ends_at = starts_at + timedelta(hours=3)
        return Event.objects.create(
            title=title,
            organizer=organizer,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            capacity=None,
            category="Зустріч",
            status=Event.PUBLISHED,
            **kwargs
        )

    @staticmethod
    def create_quick_event(
        title: str,
        organizer,
        days_from_now: int = 7,
        **kwargs
    ) -> Event:
        """Створює швидку подію (через N днів, тривалість 2 години)"""
        now = timezone.now()
        starts_at = now + timedelta(days=days_from_now)
        ends_at = starts_at + timedelta(hours=2)
        
        return Event.objects.create(
            title=title,
            organizer=organizer,
            starts_at=starts_at,
            ends_at=ends_at,
            status=Event.DRAFT,
            **kwargs
        )
