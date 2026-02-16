"""
Factory для створення нотифікацій з уніфікованими шаблонами повідомлень
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()


class NotificationFactory(ABC):
    """
    Абстрактна фабрика для створення нотифікацій
    """
    
    @abstractmethod
    def create_message(self, context: Dict[str, Any]) -> str:
        """Створити текст повідомлення на основі контексту"""
        pass
    
    @abstractmethod
    def get_notification_type(self) -> str:
        """Отримати тип нотифікації"""
        pass
    
    def create_notification(self, user: User, event, context: Dict[str, Any] = None) -> Notification:
        """
        Створити об'єкт нотифікації
        
        Args:
            user: Користувач-отримувач
            event: Подія
            context: Додатковий контекст для формування повідомлення
        """
        context = context or {}
        message = self.create_message(context)
        
        return Notification.objects.create(
            user=user,
            event=event,
            notification_type=self.get_notification_type(),
            message=message
        )


class EventUpdatedNotificationFactory(NotificationFactory):
    """Фабрика для нотифікацій про оновлення події"""
    
    def get_notification_type(self) -> str:
        return Notification.EVENT_UPDATED
    
    def create_message(self, context: Dict[str, Any]) -> str:
        event = context.get('event')
        changes = context.get('changes', [])
        
        if not changes:
            return f"Подія '{event.title}' була оновлена"
        
        changes_text = "\n".join(f"• {change}" for change in changes)
        return f"Подія '{event.title}' була оновлена:\n{changes_text}"


class EventTimeChangedNotificationFactory(NotificationFactory):
    """Фабрика для нотифікацій про зміну часу події"""
    
    def get_notification_type(self) -> str:
        return Notification.EVENT_TIME_CHANGED
    
    def create_message(self, context: Dict[str, Any]) -> str:
        event = context.get('event')
        old_start = context.get('old_start')
        new_start = context.get('new_start')
        
        if old_start and new_start:
            from django.utils import timezone
            old_formatted = timezone.localtime(old_start).strftime('%d.%m.%Y %H:%M')
            new_formatted = timezone.localtime(new_start).strftime('%d.%m.%Y %H:%M')
            return f"Час події '{event.title}' змінено з {old_formatted} на {new_formatted}"
        
        return f"Час події '{event.title}' було змінено"


class EventLocationChangedNotificationFactory(NotificationFactory):
    """Фабрика для нотифікацій про зміну локації події"""
    
    def get_notification_type(self) -> str:
        return Notification.EVENT_LOCATION_CHANGED
    
    def create_message(self, context: Dict[str, Any]) -> str:
        event = context.get('event')
        old_location = context.get('old_location') or 'не вказано'
        new_location = context.get('new_location') or 'не вказано'
        
        return f"Локацію події '{event.title}' змінено з '{old_location}' на '{new_location}'"


class EventCancelledNotificationFactory(NotificationFactory):
    """Фабрика для нотифікацій про скасування події"""
    
    def get_notification_type(self) -> str:
        return Notification.EVENT_CANCELLED
    
    def create_message(self, context: Dict[str, Any]) -> str:
        event = context.get('event')
        reason = context.get('reason', '')
        
        message = f"Подія '{event.title}' була скасована організатором"
        if reason:
            message += f". Причина: {reason}"
        
        return message + "."


class RSVPConfirmedNotificationFactory(NotificationFactory):
    """Фабрика для нотифікацій про підтвердження реєстрації"""
    
    def get_notification_type(self) -> str:
        return Notification.RSVP_CONFIRMED
    
    def create_message(self, context: Dict[str, Any]) -> str:
        event = context.get('event')
        participant = context.get('participant')
        
        return f"Користувач {participant.username} зареєструвався на подію '{event.title}'"


class RSVPCancelledNotificationFactory(NotificationFactory):
    """Фабрика для нотифікацій про скасування реєстрації"""
    
    def get_notification_type(self) -> str:
        return Notification.RSVP_CANCELLED
    
    def create_message(self, context: Dict[str, Any]) -> str:
        event = context.get('event')
        participant = context.get('participant')
        
        return f"Користувач {participant.username} скасував реєстрацію на подію '{event.title}'"


class NotificationFactoryRegistry:
    """
    Реєстр фабрик нотифікацій для централізованого управління
    """
    
    _factories = {
        Notification.EVENT_UPDATED: EventUpdatedNotificationFactory(),
        Notification.EVENT_TIME_CHANGED: EventTimeChangedNotificationFactory(),
        Notification.EVENT_LOCATION_CHANGED: EventLocationChangedNotificationFactory(),
        Notification.EVENT_CANCELLED: EventCancelledNotificationFactory(),
        Notification.RSVP_CONFIRMED: RSVPConfirmedNotificationFactory(),
        Notification.RSVP_CANCELLED: RSVPCancelledNotificationFactory(),
    }
    
    @classmethod
    def get_factory(cls, notification_type: str) -> NotificationFactory:
        """
        Отримати фабрику для конкретного типу нотифікації
        
        Args:
            notification_type: Тип нотифікації з Notification.NOTIFICATION_TYPES
            
        Returns:
            NotificationFactory: Відповідна фабрика
            
        Raises:
            ValueError: Якщо тип нотифікації не підтримується
        """
        factory = cls._factories.get(notification_type)
        if not factory:
            raise ValueError(f"Непідтримуваний тип нотифікації: {notification_type}")
        return factory
    
    @classmethod
    def create_notification(cls, notification_type: str, user: User, event, context: Dict[str, Any] = None) -> Notification:
        """
        Створити нотифікацію через відповідну фабрику
        
        Args:
            notification_type: Тип нотифікації
            user: Користувач-отримувач
            event: Подія
            context: Контекст для формування повідомлення
            
        Returns:
            Notification: Створена нотифікація
        """
        factory = cls.get_factory(notification_type)
        return factory.create_notification(user, event, context)
    
    @classmethod
    def register_factory(cls, notification_type: str, factory: NotificationFactory):
        """
        Зареєструвати нову фабрику (для розширення функціональності)
        
        Args:
            notification_type: Тип нотифікації
            factory: Фабрика для цього типу
        """
        cls._factories[notification_type] = factory
