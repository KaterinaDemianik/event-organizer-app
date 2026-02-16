"""
DTO Pattern та PersonalScheduleService для роботи з персональним розкладом

Цей модуль реалізує Data Transfer Object (DTO) для передачі даних про події
та сервіс для формування персонального розкладу користувача.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, List, Set

from django.db.models import Q, QuerySet

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
    
    def to_dict(self) -> dict:
        """Конвертує DTO в словник для JSON серіалізації"""
        return {
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
            QuerySet подій
        """
        from .models import Event
        
        user_events = Q(organizer=user)
        registered_events = Q(
            status=Event.PUBLISHED,
            rsvps__user=user
        )
        
        return Event.objects.filter(
            user_events | registered_events
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
