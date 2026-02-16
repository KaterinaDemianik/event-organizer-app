"""
State Pattern для управління станами подій

Цей модуль реалізує State Pattern для контролю переходів між станами події
(draft -> published -> cancelled/archived) з валідацією бізнес-правил.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

from django.utils import timezone

if TYPE_CHECKING:
    from .models import Event


class EventState(ABC):
    """Абстрактний базовий клас для станів події"""

    name: str = ""
    
    @abstractmethod
    def can_edit(self) -> bool:
        """Чи можна редагувати подію в цьому стані"""
        raise NotImplementedError
    
    @abstractmethod
    def can_cancel(self) -> bool:
        """Чи можна скасувати подію в цьому стані"""
        raise NotImplementedError
    
    @abstractmethod
    def can_archive(self) -> bool:
        """Чи можна архівувати подію в цьому стані"""
        raise NotImplementedError
    
    @abstractmethod
    def can_publish(self) -> bool:
        """Чи можна опублікувати подію в цьому стані"""
        raise NotImplementedError
    
    @abstractmethod
    def get_allowed_transitions(self) -> Set[str]:
        """Повертає множину дозволених переходів з цього стану"""
        raise NotImplementedError
    
    def get_available_actions(self) -> List[str]:
        """Повертає список доступних дій для цього стану"""
        actions = []
        if self.can_edit():
            actions.append("edit")
        if self.can_publish():
            actions.append("publish")
        if self.can_cancel():
            actions.append("cancel")
        if self.can_archive():
            actions.append("archive")
        return actions


class DraftState(EventState):
    """Стан чернетки - подія ще не опублікована"""

    name = "draft"
    
    def can_edit(self) -> bool:
        return True
    
    def can_cancel(self) -> bool:
        return True
    
    def can_archive(self) -> bool:
        return False
    
    def can_publish(self) -> bool:
        return True
    
    def get_allowed_transitions(self) -> Set[str]:
        return {"published", "cancelled"}


class PublishedState(EventState):
    """Стан опублікованої події"""

    name = "published"
    
    def can_edit(self) -> bool:
        return True
    
    def can_cancel(self) -> bool:
        return True
    
    def can_archive(self) -> bool:
        return True
    
    def can_publish(self) -> bool:
        return False
    
    def get_allowed_transitions(self) -> Set[str]:
        return {"cancelled", "archived"}


class CancelledState(EventState):
    """Стан скасованої події"""

    name = "cancelled"
    
    def can_edit(self) -> bool:
        return False
    
    def can_cancel(self) -> bool:
        return False
    
    def can_archive(self) -> bool:
        return False
    
    def can_publish(self) -> bool:
        return False
    
    def get_allowed_transitions(self) -> Set[str]:
        return set()


class ArchivedState(EventState):
    """Стан архівованої події"""

    name = "archived"
    
    def can_edit(self) -> bool:
        return False
    
    def can_cancel(self) -> bool:
        return False
    
    def can_archive(self) -> bool:
        return False
    
    def can_publish(self) -> bool:
        return False
    
    def get_allowed_transitions(self) -> Set[str]:
        return set()


STATE_CLASSES: Dict[str, EventState] = {
    "draft": DraftState(),
    "published": PublishedState(),
    "cancelled": CancelledState(),
    "archived": ArchivedState(),
}


class EventStateManager:
    """
    Менеджер станів подій - центральна точка для роботи зі станами
    
    Реалізує State Pattern для контролю переходів між станами події
    з валідацією бізнес-правил.
    """

    @staticmethod
    def get_state(status: str) -> EventState:
        """Отримати об'єкт стану за статусом"""
        return STATE_CLASSES.get(status, STATE_CLASSES["draft"])
    
    @staticmethod
    def can_transition(from_status: str, to_status: str) -> bool:
        """
        Перевірити, чи можливий перехід між станами
        
        Args:
            from_status: Поточний статус
            to_status: Цільовий статус
            
        Returns:
            True якщо перехід дозволений
        """
        state = EventStateManager.get_state(from_status)
        return to_status in state.get_allowed_transitions()
    
    @staticmethod
    def validate_transition(event: "Event", new_status: str) -> Tuple[bool, Optional[str]]:
        """
        Валідація переходу з урахуванням бізнес-правил
        
        Args:
            event: Подія для перевірки
            new_status: Цільовий статус
            
        Returns:
            Tuple (is_valid, error_message)
            - is_valid: True якщо перехід валідний
            - error_message: Повідомлення про помилку або None
        """
        current_status = event.status
        
        if current_status == new_status:
            return True, None
        
        if not EventStateManager.can_transition(current_status, new_status):
            return False, f"Перехід з '{current_status}' до '{new_status}' неможливий"
        
        if new_status == "archived":
            now = timezone.now()
            if event.ends_at >= now:
                return False, "Архівувати можна лише завершені події"
            if current_status != "published":
                return False, "Архівувати можна лише опубліковані події"
        
        return True, None
    
    @staticmethod
    def get_available_actions(event: "Event") -> List[str]:
        """
        Отримати список доступних дій для події
        
        Args:
            event: Подія
            
        Returns:
            Список доступних дій (edit, publish, cancel, archive)
        """
        state = EventStateManager.get_state(event.status)
        actions = state.get_available_actions()
        
        if "archive" in actions:
            now = timezone.now()
            if event.ends_at >= now:
                actions.remove("archive")
        
        return actions
    
    @staticmethod
    def can_edit(event: "Event") -> bool:
        """Перевірити, чи можна редагувати подію"""
        state = EventStateManager.get_state(event.status)
        return state.can_edit()
    
    @staticmethod
    def can_cancel(event: "Event") -> bool:
        """Перевірити, чи можна скасувати подію"""
        state = EventStateManager.get_state(event.status)
        return state.can_cancel()
    
    @staticmethod
    def can_archive(event: "Event") -> bool:
        """Перевірити, чи можна архівувати подію (з урахуванням часу)"""
        state = EventStateManager.get_state(event.status)
        if not state.can_archive():
            return False
        now = timezone.now()
        return event.ends_at < now
