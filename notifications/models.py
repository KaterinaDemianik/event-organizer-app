from django.db import models
from django.contrib.auth import get_user_model


class Notification(models.Model):
    """
    Модель для зберігання сповіщень користувачів про зміни в подіях
    """
    EVENT_UPDATED = 'event_updated'
    EVENT_CANCELLED = 'event_cancelled'
    EVENT_TIME_CHANGED = 'event_time_changed'
    EVENT_LOCATION_CHANGED = 'event_location_changed'
    
    NOTIFICATION_TYPES = [
        (EVENT_UPDATED, 'Подію оновлено'),
        (EVENT_CANCELLED, 'Подію скасовано'),
        (EVENT_TIME_CHANGED, 'Час події змінено'),
        (EVENT_LOCATION_CHANGED, 'Локацію змінено'),
    ]
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='Користувач, який отримує сповіщення'
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='Подія, про яку сповіщення'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default=EVENT_UPDATED
    )
    message = models.TextField(
        help_text='Текст сповіщення'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Чи прочитане сповіщення'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}: {self.event.title}"
