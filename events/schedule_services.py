"""
DTO Pattern та PersonalScheduleService для роботи з персональним розкладом

Цей модуль реалізує Data Transfer Object (DTO) для передачі даних про події
та сервіс для формування персонального розкладу користувача.

Також реалізує Decorator Pattern для обгорток розкладу:
- FilteredScheduleDecorator: фільтрація за параметрами
- HighlightedScheduleDecorator: підсвічування подій
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Protocol, Set

from django.db.models import Q, QuerySet
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


@dataclass
class ScheduleEntry:
    """
    Data Transfer Object для запису в розкладі
    
    Інкапсулює дані про подію для відображення в календарі,
    уникаючи передачі повних ORM-об'єктів у presentation layer.
    """
    
    event_id: int
    title: str
    starts_at: datetime
    ends_at: datetime
    status: str
    location: str
    description: str
    is_organizer: bool
    has_rsvp: bool
    highlight_reason: str = ""
    rsvp_count: int = 0
    
    def to_dict(self) -> dict:
        """Конвертує DTO в словник для JSON серіалізації"""
        result = {
            "id": self.event_id,
            "title": self.title,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "status": self.status,
            "location": self.location,
            "description": self.description,
            "is_organizer": self.is_organizer,
            "has_rsvp": self.has_rsvp,
        }
        if self.highlight_reason:
            result["highlight_reason"] = self.highlight_reason
        return result


class ScheduleProvider(Protocol):
    """Протокол для провайдерів розкладу (Decorator Pattern)"""
    
    def get_entries(self, user: "AbstractUser") -> List[ScheduleEntry]:
        """Отримати записи розкладу для користувача"""
        ...


class BaseScheduleProvider:
    """
    Базовий провайдер розкладу
    
    Адаптер до PersonalScheduleService для використання в ланцюжку декораторів.
    """
    
    def get_entries(self, user: "AbstractUser") -> List[ScheduleEntry]:
        """Отримати записи розкладу через PersonalScheduleService"""
        return PersonalScheduleService.get_user_schedule_entries(user)


class ScheduleDecorator(ABC):
    """
    Абстрактний декоратор для розкладу
    
    Базовий клас для всіх декораторів, що обгортають ScheduleProvider.
    """
    
    def __init__(self, provider: ScheduleProvider):
        self._provider = provider
    
    @abstractmethod
    def get_entries(self, user: "AbstractUser") -> List[ScheduleEntry]:
        """Отримати записи розкладу (має бути реалізовано в підкласах)"""
        pass


class FilteredScheduleDecorator(ScheduleDecorator):
    """
    Декоратор для фільтрації записів розкладу
    
    Підтримує фільтри:
    - only_upcoming: тільки майбутні події
    - only_organizer: тільки події, де користувач організатор
    - only_published: тільки опубліковані події
    """
    
    def __init__(
        self, 
        provider: ScheduleProvider,
        only_upcoming: bool = False,
        only_organizer: bool = False,
        only_published: bool = False
    ):
        super().__init__(provider)
        self._only_upcoming = only_upcoming
        self._only_organizer = only_organizer
        self._only_published = only_published
    
    def get_entries(self, user: "AbstractUser") -> List[ScheduleEntry]:
        """Отримати відфільтровані записи розкладу"""
        entries = self._provider.get_entries(user)
        
        if self._only_upcoming:
            now = timezone.now()
            entries = [e for e in entries if e.starts_at > now]
        
        if self._only_organizer:
            entries = [e for e in entries if e.is_organizer]
        
        if self._only_published:
            entries = [e for e in entries if e.status == "published"]
        
        return entries


class HighlightedScheduleDecorator(ScheduleDecorator):
    """
    Декоратор для підсвічування записів розкладу
    
    Підтримує режими підсвічування:
    - soon: події, що починаються в межах 24 годин
    - organizer: події, де користувач організатор
    - popular: події з rsvp_count >= 5
    """
    
    HIGHLIGHT_SOON = "soon"
    HIGHLIGHT_ORGANIZER = "organizer"
    HIGHLIGHT_POPULAR = "popular"
    
    POPULAR_THRESHOLD = 5
    SOON_HOURS = 24
    
    def __init__(self, provider: ScheduleProvider, highlight_mode: str = ""):
        super().__init__(provider)
        self._highlight_mode = highlight_mode
    
    def get_entries(self, user: "AbstractUser") -> List[ScheduleEntry]:
        """Отримати записи з підсвічуванням"""
        entries = self._provider.get_entries(user)
        
        if not self._highlight_mode:
            return entries
        
        now = timezone.now()
        soon_threshold = now + timedelta(hours=self.SOON_HOURS)
        
        result = []
        for entry in entries:
            highlight_reason = self._get_highlight_reason(entry, now, soon_threshold)
            if highlight_reason:
                entry = replace(entry, highlight_reason=highlight_reason)
            result.append(entry)
        
        return result
    
    def _get_highlight_reason(
        self, 
        entry: ScheduleEntry, 
        now: datetime, 
        soon_threshold: datetime
    ) -> str:
        """Визначити причину підсвічування для запису"""
        if self._highlight_mode == self.HIGHLIGHT_SOON:
            if now < entry.starts_at <= soon_threshold:
                return "soon"
        
        elif self._highlight_mode == self.HIGHLIGHT_ORGANIZER:
            if entry.is_organizer:
                return "organizer"
        
        elif self._highlight_mode == self.HIGHLIGHT_POPULAR:
            if entry.rsvp_count >= self.POPULAR_THRESHOLD:
                return "popular"
        
        return ""


class PersonalScheduleService:
    """
    Сервіс для роботи з персональним розкладом користувача
    
    Реалізує логіку отримання подій користувача з оптимізацією
    для уникнення N+1 проблеми.
    """
    
    @staticmethod
    def get_user_events_queryset(user: "AbstractUser") -> QuerySet:
        """
        Отримати QuerySet подій користувача (організовані + зареєстровані)
        
        Args:
            user: Користувач
            
        Returns:
            QuerySet подій з анотацією rsvp_count
        """
        from django.db.models import Count
        from .models import Event
        
        user_events = Q(organizer=user)
        registered_events = Q(
            status=Event.PUBLISHED,
            rsvps__user=user
        )
        
        return Event.objects.filter(
            user_events | registered_events
        ).annotate(
            rsvp_count=Count("rsvps", filter=Q(rsvps__status="going"))
        ).distinct().order_by("starts_at")
    
    @staticmethod
    def get_user_rsvp_event_ids(user: "AbstractUser") -> Set[int]:
        """
        Отримати множину ID подій, на які користувач зареєстрований
        
        Оптимізація: один запит замість .exists() для кожної події
        
        Args:
            user: Користувач
            
        Returns:
            Set з ID подій
        """
        from tickets.models import RSVP
        
        return set(
            RSVP.objects.filter(user=user)
            .values_list("event_id", flat=True)
        )
    
    @staticmethod
    def get_user_schedule_entries(user: "AbstractUser") -> List[ScheduleEntry]:
        """
        Отримати список ScheduleEntry для користувача
        
        Оптимізовано для уникнення N+1:
        - Один запит для подій
        - Один запит для RSVP event_ids
        
        Args:
            user: Користувач
            
        Returns:
            Список ScheduleEntry DTO
        """
        events_qs = PersonalScheduleService.get_user_events_queryset(user)
        rsvp_event_ids = PersonalScheduleService.get_user_rsvp_event_ids(user)
        
        entries = []
        for event in events_qs:
            entry = ScheduleEntry(
                event_id=event.id,
                title=event.title,
                starts_at=event.starts_at,
                ends_at=event.ends_at,
                status=event.status,
                location=event.location or "",
                description=event.description or "",
                is_organizer=(event.organizer_id == user.id),
                has_rsvp=(event.id in rsvp_event_ids),
                rsvp_count=getattr(event, "rsvp_count", 0),
            )
            entries.append(entry)
        
        return entries
    
    @staticmethod
    def get_schedule_json_data(user: "AbstractUser") -> str:
        """
        Отримати JSON-дані розкладу для JavaScript календаря
        
        Args:
            user: Користувач
            
        Returns:
            JSON-рядок з даними подій
        """
        entries = PersonalScheduleService.get_user_schedule_entries(user)
        data = [entry.to_dict() for entry in entries]
        return json.dumps(data)
