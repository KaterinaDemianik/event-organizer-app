"""
Сервіси для роботи зі сповіщеннями
"""
from django.utils import timezone
from notifications.models import Notification


class NotificationService:
    """
    Сервіс для створення та управління сповіщеннями
    """
    
    
    @staticmethod
    def create_event_update_notification(event, old_event_data):
        """
        Створити сповіщення про зміни в події
        
        Args:
            event: Оновлена подія
            old_event_data: Словник з попередніми значеннями полів
        """
        changes = []
        context = {'event': event}
        
        # Перевірити зміну часу
        time_changed = (old_event_data.get('starts_at') != event.starts_at or 
                       old_event_data.get('ends_at') != event.ends_at)
        if time_changed:
            old_start = old_event_data.get('starts_at')
            new_start = event.starts_at
            if old_start and new_start:
                changes.append(f"Час події змінено з {timezone.localtime(old_start).strftime('%d.%m.%Y %H:%M')} на {timezone.localtime(new_start).strftime('%d.%m.%Y %H:%M')}")
                context.update({'old_start': old_start, 'new_start': new_start})
        
        # Перевірити зміну локації
        location_changed = old_event_data.get('location') != event.location
        if location_changed:
            old_loc = old_event_data.get('location')
            new_loc = event.location
            changes.append(f"Локацію змінено з '{old_loc or 'не вказано'}' на '{new_loc or 'не вказано'}'")
            context.update({'old_location': old_loc, 'new_location': new_loc})
        
        # Перевірити зміну назви
        if old_event_data.get('title') != event.title:
            changes.append(f"Назву змінено на '{event.title}'")
        
        # Перевірити зміну опису
        if old_event_data.get('description') != event.description:
            changes.append("Опис події оновлено")
        
        # Визначити тип нотифікації та створити сповіщення
        if changes:
            context['changes'] = changes
            
            # Використовуємо специфічні типи для одиночних змін
            if time_changed and not location_changed and len(changes) == 1:
                notification_type = Notification.EVENT_TIME_CHANGED
            elif location_changed and not time_changed and len(changes) == 1:
                notification_type = Notification.EVENT_LOCATION_CHANGED
            else:
                # Для комплексних змін використовуємо загальний тип
                notification_type = Notification.EVENT_UPDATED
            
            return NotificationService.notify_event_participants_with_factory(
                event, notification_type, context
            )
        
        return 0
    
    @staticmethod
    def create_event_cancelled_notification(event):
        """
        Створити сповіщення про скасування події
        """
        context = {'event': event}
        return NotificationService.notify_event_participants_with_factory(
            event, 
            Notification.EVENT_CANCELLED, 
            context
        )
    
    @staticmethod
    def notify_event_participants_with_factory(event, notification_type, context):
        """
        Створити сповіщення для всіх учасників події через фабрику
        
        Args:
            event: Подія
            notification_type: Тип сповіщення
            context: Контекст для формування повідомлення
        """
        from tickets.models import RSVP
        from notifications.factories import NotificationFactoryRegistry
        
        # Отримати всіх учасників події (крім організатора)
        participants = RSVP.objects.filter(
            event=event,
            status='going'
        ).exclude(
            user=event.organizer
        ).select_related('user')
        
        # Отримати фабрику та згенерувати повідомлення один раз
        factory = NotificationFactoryRegistry.get_factory(notification_type)
        message = factory.create_message(context)
        
        # Створити список нотифікацій для bulk_create
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
