"""
Builder Pattern для поетапного створення складних об'єктів подій.
Дозволяє гнучко налаштовувати події перед створенням.
"""
from datetime import datetime
from typing import Optional

from .models import Event


class EventBuilder:
    """
    Builder для створення події з можливістю поетапного налаштування.
    Використовується для складних сценаріїв створення подій.
    """

    def __init__(self):
        self._title: Optional[str] = None
        self._organizer = None
        self._description: str = ""
        self._location: str = ""
        self._starts_at: Optional[datetime] = None
        self._ends_at: Optional[datetime] = None
        self._capacity: Optional[int] = None
        self._status: str = Event.DRAFT
        self._category: str = ""
        self._latitude: Optional[float] = None
        self._longitude: Optional[float] = None

    def with_title(self, title: str) -> 'EventBuilder':
        """Встановлює назву події"""
        self._title = title
        return self

    def with_organizer(self, organizer) -> 'EventBuilder':
        """Встановлює організатора"""
        self._organizer = organizer
        return self

    def with_description(self, description: str) -> 'EventBuilder':
        """Встановлює опис"""
        self._description = description
        return self

    def with_location(self, location: str) -> 'EventBuilder':
        """Встановлює локацію"""
        self._location = location
        return self

    def with_coordinates(self, latitude: float, longitude: float) -> 'EventBuilder':
        """Встановлює географічні координати"""
        self._latitude = latitude
        self._longitude = longitude
        return self

    def with_dates(self, starts_at: datetime, ends_at: datetime) -> 'EventBuilder':
        """Встановлює дати початку та закінчення"""
        self._starts_at = starts_at
        self._ends_at = ends_at
        return self

    def with_capacity(self, capacity: int) -> 'EventBuilder':
        """Встановлює максимальну кількість учасників"""
        self._capacity = capacity
        return self

    def with_status(self, status: str) -> 'EventBuilder':
        """Встановлює статус події"""
        self._status = status
        return self

    def with_category(self, category: str) -> 'EventBuilder':
        """Встановлює категорію"""
        self._category = category
        return self

    def as_draft(self) -> 'EventBuilder':
        """Встановлює статус "чернетка" """
        self._status = Event.DRAFT
        return self

    def as_published(self) -> 'EventBuilder':
        """Встановлює статус "опубліковано" """
        self._status = Event.PUBLISHED
        return self

    def build(self) -> Event:
        """
        Створює та повертає об'єкт події.
        Перевіряє наявність обов'язкових полів.
        """
        if not self._title:
            raise ValueError("Назва події є обов'язковою")
        if not self._organizer:
            raise ValueError("Організатор є обов'язковим")

        event = Event(
            title=self._title,
            organizer=self._organizer,
            description=self._description,
            location=self._location,
            starts_at=self._starts_at,
            ends_at=self._ends_at,
            capacity=self._capacity,
            status=self._status,
            category=self._category,
            latitude=self._latitude,
            longitude=self._longitude,
        )
        
        event.save()
        return event

    def reset(self) -> 'EventBuilder':
        """Скидає всі налаштування до початкових значень"""
        self.__init__()
        return self


class ConferenceEventBuilder(EventBuilder):
    """Спеціалізований builder для конференцій"""

    def __init__(self):
        super().__init__()
        self._category = "Конференція"
        self._capacity = 100

    def with_large_capacity(self) -> 'ConferenceEventBuilder':
        """Встановлює велику місткість (500 осіб)"""
        self._capacity = 500
        return self


class WorkshopEventBuilder(EventBuilder):
    """Спеціалізований builder для майстер-класів"""

    def __init__(self):
        super().__init__()
        self._category = "Майстер-клас"
        self._capacity = 20

    def with_small_group(self) -> 'WorkshopEventBuilder':
        """Встановлює малу групу (10 осіб)"""
        self._capacity = 10
        return self
