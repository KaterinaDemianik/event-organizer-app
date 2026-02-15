"""
Observer Pattern через Django Signals.
Реагування на зміни в подіях та RSVP без жорстких залежностей.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from .models import Event
from tickets.models import RSVP


@receiver(pre_save, sender=Event)
def event_pre_save(sender, instance, **kwargs):
    """
    Зберігає попередній стан події перед збереженням.
    Використовує атрибут на інстансі замість глобального словника.
    """
    if instance.pk:
        try:
            old_event = Event.objects.get(pk=instance.pk)
            # Зберігаємо попередній статус на самому інстансі
            instance._previous_status = old_event.status
        except Event.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Event)
def event_post_save(sender, instance, created, **kwargs):
    """Обробляє зміни в події після збереження"""
    from notifications.services import NotificationService
    
    if created:
        # Нова подія створена
        pass
    else:
        # Подія оновлена - перевіряємо зміну статусу
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status and previous_status != Event.CANCELLED and instance.status == Event.CANCELLED:
            NotificationService.create_event_cancelled_notification(instance)


@receiver(post_save, sender=RSVP)
def rsvp_created(sender, instance, created, **kwargs):
    """Обробляє створення нового RSVP"""
    from notifications.models import Notification
    
    if created:
        # Сповіщення організатору про нову реєстрацію
        Notification.objects.create(
            user=instance.event.organizer,
            event=instance.event,
            notification_type=Notification.RSVP_CONFIRMED,
            message=f"Користувач {instance.user.username} зареєструвався на подію '{instance.event.title}'"
        )


@receiver(post_delete, sender=RSVP)
def rsvp_deleted(sender, instance, **kwargs):
    """Обробляє видалення RSVP (скасування реєстрації)"""
    from notifications.models import Notification
    
    # Сповіщення організатору про скасування реєстрації
    Notification.objects.create(
        user=instance.event.organizer,
        event=instance.event,
        notification_type=Notification.RSVP_CANCELLED,
        message=f"Користувач {instance.user.username} скасував реєстрацію на подію '{instance.event.title}'"
    )
