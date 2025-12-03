"""
Сервіси для роботи зі сповіщеннями
"""
from django.db.models import Q
from notifications.models import Notification


class NotificationService:
    """
    Сервіс для створення та управління сповіщеннями
    """
    
    @staticmethod
    def notify_event_participants(event, notification_type, message):
        """
        Створити сповіщення для всіх учасників події (крім організатора)
        
        Args:
            event: Подія
            notification_type: Тип сповіщення (EVENT_UPDATED, EVENT_CANCELLED, тощо)
            message: Текст сповіщення
        """
        from tickets.models import RSVP
        
        # Отримати всіх учасників події (крім організатора)
        participants = RSVP.objects.filter(
            event=event,
            status='going'
        ).exclude(
            user=event.organizer
        ).select_related('user')
        
        # Створити сповіщення для кожного учасника
        notifications = []
        for rsvp in participants:
            notifications.append(
                Notification(
                    user=rsvp.user,
                    event=event,
                    notification_type=notification_type,
                    message=message
                )
            )
        
        # Bulk create для оптимізації
        if notifications:
            Notification.objects.bulk_create(notifications)
        
        return len(notifications)
    
    @staticmethod
    def create_event_update_notification(event, old_event_data):
        """
        Створити сповіщення про зміни в події
        
        Args:
            event: Оновлена подія
            old_event_data: Словник з попередніми значеннями полів
        """
        changes = []
        notification_type = Notification.EVENT_UPDATED
        
        # Перевірити зміну часу
        if old_event_data.get('starts_at') != event.starts_at or old_event_data.get('ends_at') != event.ends_at:
            old_start = old_event_data.get('starts_at').strftime('%d.%m.%Y %H:%M')
            new_start = event.starts_at.strftime('%d.%m.%Y %H:%M')
            changes.append(f"Час події змінено з {old_start} на {new_start}")
            notification_type = Notification.EVENT_TIME_CHANGED
        
        # Перевірити зміну локації
        if old_event_data.get('location') != event.location:
            old_loc = old_event_data.get('location') or 'не вказано'
            new_loc = event.location or 'не вказано'
            changes.append(f"Локацію змінено з '{old_loc}' на '{new_loc}'")
            if notification_type == Notification.EVENT_UPDATED:
                notification_type = Notification.EVENT_LOCATION_CHANGED
        
        # Перевірити зміну назви
        if old_event_data.get('title') != event.title:
            changes.append(f"Назву змінено на '{event.title}'")
        
        # Перевірити зміну опису
        if old_event_data.get('description') != event.description:
            changes.append("Опис події оновлено")
        
        # Якщо є зміни - створити сповіщення
        if changes:
            message = f"Подія '{event.title}' була оновлена:\n" + "\n".join(f"• {change}" for change in changes)
            return NotificationService.notify_event_participants(event, notification_type, message)
        
        return 0
    
    @staticmethod
    def create_event_cancelled_notification(event):
        """
        Створити сповіщення про скасування події
        """
        message = f"Подія '{event.title}' була скасована організатором."
        return NotificationService.notify_event_participants(
            event,
            Notification.EVENT_CANCELLED,
            message
        )
