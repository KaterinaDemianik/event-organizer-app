"""
Тести для signals.py - Observer Pattern через Django Signals
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from events.models import Event
from events.signals import event_pre_save, event_post_save, rsvp_created, rsvp_deleted
from tickets.models import RSVP
from notifications.models import Notification


class SignalsObserverPatternTestCase(TestCase):
    """Тести для Observer Pattern через Django Signals"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_event_pre_save_new_event(self):
        """Тест pre_save сигналу для нової події"""
        new_event = Event(
            title="New Event",
            description="New Description",
            starts_at=timezone.now() + timedelta(days=2),
            ends_at=timezone.now() + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )
        
        # Викликаємо сигнал вручну
        event_pre_save(Event, new_event)
        
        # Для нової події _previous_status має бути None
        self.assertIsNone(getattr(new_event, '_previous_status', None))

    def test_event_pre_save_existing_event(self):
        """Тест pre_save сигналу для існуючої події"""
        # Змінюємо статус існуючої події
        self.event.status = Event.CANCELLED
        
        # Викликаємо сигнал вручну
        event_pre_save(Event, self.event)
        
        # Має зберегти попередній статус
        self.assertEqual(self.event._previous_status, Event.PUBLISHED)

    def test_event_pre_save_nonexistent_event_with_pk(self):
        """Тест pre_save сигналу для події з pk але яка не існує в БД"""
        fake_event = Event(
            pk=999999,  # Неіснуючий pk
            title="Fake Event",
            description="Fake Description",
            starts_at=timezone.now() + timedelta(days=2),
            ends_at=timezone.now() + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )
        
        # Викликаємо сигнал вручну
        event_pre_save(Event, fake_event)
        
        # Має встановити _previous_status в None якщо подія не знайдена
        self.assertIsNone(fake_event._previous_status)

    def test_event_post_save_created(self):
        """Тест post_save сигналу для створеної події"""
        # Створюємо нову подію (created=True)
        new_event = Event.objects.create(
            title="Created Event",
            description="Created Description",
            starts_at=timezone.now() + timedelta(days=3),
            ends_at=timezone.now() + timedelta(days=3, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )
        
        # Викликаємо сигнал вручну для created=True
        event_post_save(Event, new_event, created=True)
        
        # Для нової події нічого особливого не відбувається
        # Просто перевіряємо що сигнал не падає
        self.assertTrue(True)

    @patch('notifications.services.NotificationService.create_event_cancelled_notification')
    def test_event_post_save_cancelled(self, mock_notification):
        """Тест post_save сигналу при скасуванні події"""
        # Встановлюємо попередній статус
        self.event._previous_status = Event.PUBLISHED
        self.event.status = Event.CANCELLED
        
        # Викликаємо сигнал вручну
        event_post_save(Event, self.event, created=False)
        
        # Перевіряємо що викликано створення сповіщення
        mock_notification.assert_called_once_with(self.event)

    @patch('notifications.services.NotificationService.create_event_cancelled_notification')
    def test_event_post_save_not_cancelled(self, mock_notification):
        """Тест post_save сигналу при зміні статусу не на CANCELLED"""
        # Встановлюємо попередній статус
        self.event._previous_status = Event.DRAFT
        self.event.status = Event.PUBLISHED
        
        # Викликаємо сигнал вручну
        event_post_save(Event, self.event, created=False)
        
        # Сповіщення не має бути створено
        mock_notification.assert_not_called()

    @patch('notifications.services.NotificationService.create_event_cancelled_notification')
    def test_event_post_save_already_cancelled(self, mock_notification):
        """Тест post_save сигналу коли подія вже була скасована"""
        # Встановлюємо попередній статус як CANCELLED
        self.event._previous_status = Event.CANCELLED
        self.event.status = Event.CANCELLED
        
        # Викликаємо сигнал вручну
        event_post_save(Event, self.event, created=False)
        
        # Сповіщення не має бути створено (подія вже була скасована)
        mock_notification.assert_not_called()

    @patch('notifications.services.NotificationService.create_event_cancelled_notification')
    def test_event_post_save_no_previous_status(self, mock_notification):
        """Тест post_save сигналу без попереднього статусу"""
        # Не встановлюємо _previous_status
        self.event.status = Event.CANCELLED
        
        # Викликаємо сигнал вручну
        event_post_save(Event, self.event, created=False)
        
        # Сповіщення не має бути створено (немає попереднього статусу)
        mock_notification.assert_not_called()

    @patch('notifications.factories.NotificationFactoryRegistry.create_notification')
    def test_rsvp_created_signal(self, mock_factory):
        """Тест сигналу створення RSVP"""
        # Створюємо RSVP об'єкт без збереження в БД
        rsvp = RSVP(
            user=self.user,
            event=self.event,
            status="going"
        )
        
        # Викликаємо сигнал вручну для created=True
        rsvp_created(RSVP, rsvp, created=True)
        
        # Перевіряємо що викликано фабрику сповіщень
        mock_factory.assert_called_once_with(
            notification_type=Notification.RSVP_CONFIRMED,
            user=self.event.organizer,
            event=self.event,
            context={
                'event': self.event,
                'participant': self.user
            }
        )

    @patch('notifications.factories.NotificationFactoryRegistry.create_notification')
    def test_rsvp_created_signal_updated(self, mock_factory):
        """Тест сигналу оновлення RSVP (не created)"""
        # Створюємо RSVP об'єкт без збереження в БД
        rsvp = RSVP(
            user=self.user,
            event=self.event,
            status="going"
        )
        
        # Викликаємо сигнал вручну для created=False
        rsvp_created(RSVP, rsvp, created=False)
        
        # Фабрика не має бути викликана для оновлення
        mock_factory.assert_not_called()

    @patch('notifications.factories.NotificationFactoryRegistry.create_notification')
    def test_rsvp_deleted_signal(self, mock_factory):
        """Тест сигналу видалення RSVP"""
        # Створюємо RSVP об'єкт без збереження в БД
        rsvp = RSVP(
            user=self.user,
            event=self.event,
            status="going"
        )
        
        # Викликаємо сигнал видалення вручну
        rsvp_deleted(RSVP, rsvp)
        
        # Перевіряємо що викликано фабрику сповіщень
        mock_factory.assert_called_once_with(
            notification_type=Notification.RSVP_CANCELLED,
            user=self.event.organizer,
            event=self.event,
            context={
                'event': self.event,
                'participant': self.user
            }
        )

    def test_signals_integration_rsvp_creation(self):
        """Інтеграційний тест створення RSVP через сигнали"""
        initial_notifications = Notification.objects.count()
        
        # Створюємо RSVP - має автоматично тригернути сигнал
        RSVP.objects.create(
            user=self.user,
            event=self.event,
            status="going"
        )
        
        # Перевіряємо що створено сповіщення
        final_notifications = Notification.objects.count()
        self.assertGreater(final_notifications, initial_notifications)

    def test_signals_integration_rsvp_deletion(self):
        """Інтеграційний тест видалення RSVP через сигнали"""
        # Створюємо RSVP
        rsvp = RSVP.objects.create(
            user=self.user,
            event=self.event,
            status="going"
        )
        
        initial_notifications = Notification.objects.count()
        
        # Видаляємо RSVP - має автоматично тригернути сигнал
        rsvp.delete()
        
        # Перевіряємо що створено сповіщення про скасування
        final_notifications = Notification.objects.count()
        self.assertGreater(final_notifications, initial_notifications)

    @patch('notifications.services.NotificationService.create_event_cancelled_notification')
    def test_signals_integration_event_cancellation(self, mock_notification):
        """Інтеграційний тест скасування події через сигнали"""
        # Спочатку зберігаємо подію щоб встановити попередній статус
        self.event.save()  # Це встановить _previous_status через pre_save
        
        # Тепер змінюємо статус на CANCELLED - має тригернути сигнал
        self.event.status = Event.CANCELLED
        self.event.save()
        
        # Перевіряємо що викликано створення сповіщення
        mock_notification.assert_called_once_with(self.event)
