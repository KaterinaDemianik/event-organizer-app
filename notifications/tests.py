from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from tickets.models import RSVP
from notifications.models import Notification
from notifications.factories import (
    NotificationFactoryRegistry,
    EventUpdatedNotificationFactory,
    EventTimeChangedNotificationFactory,
    EventLocationChangedNotificationFactory,
    EventCancelledNotificationFactory,
    RSVPConfirmedNotificationFactory,
    RSVPCancelledNotificationFactory
)

User = get_user_model()


class NotificationFactoryTests(TestCase):
    """Тести для Factory патерну нотифікацій"""
    
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant = User.objects.create_user(username="participant", password="pass")
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            location="Test Location",
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )
    
    def test_event_updated_factory(self):
        """Тест фабрики для оновлення події"""
        factory = EventUpdatedNotificationFactory()
        context = {
            'event': self.event,
            'changes': ['Назву змінено', 'Опис оновлено']
        }
        
        notification = factory.create_notification(
            user=self.participant,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.notification_type, Notification.EVENT_UPDATED)
        self.assertIn("Test Event", notification.message)
        self.assertIn("Назву змінено", notification.message)
        self.assertIn("Опис оновлено", notification.message)
    
    def test_event_time_changed_factory(self):
        """Тест фабрики для зміни часу події"""
        factory = EventTimeChangedNotificationFactory()
        old_start = timezone.now() + timedelta(days=1)
        new_start = timezone.now() + timedelta(days=2)
        
        context = {
            'event': self.event,
            'old_start': old_start,
            'new_start': new_start
        }
        
        notification = factory.create_notification(
            user=self.participant,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.notification_type, Notification.EVENT_TIME_CHANGED)
        self.assertIn("Test Event", notification.message)
        self.assertIn("змінено з", notification.message)
    
    def test_event_location_changed_factory(self):
        """Тест фабрики для зміни локації події"""
        factory = EventLocationChangedNotificationFactory()
        context = {
            'event': self.event,
            'old_location': 'Old Location',
            'new_location': 'New Location'
        }
        
        notification = factory.create_notification(
            user=self.participant,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.notification_type, Notification.EVENT_LOCATION_CHANGED)
        self.assertIn("Test Event", notification.message)
        self.assertIn("Old Location", notification.message)
        self.assertIn("New Location", notification.message)
    
    def test_event_cancelled_factory(self):
        """Тест фабрики для скасування події"""
        factory = EventCancelledNotificationFactory()
        context = {
            'event': self.event,
            'reason': 'Технічні проблеми'
        }
        
        notification = factory.create_notification(
            user=self.participant,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.notification_type, Notification.EVENT_CANCELLED)
        self.assertIn("Test Event", notification.message)
        self.assertIn("скасована", notification.message)
        self.assertIn("Технічні проблеми", notification.message)
    
    def test_rsvp_confirmed_factory(self):
        """Тест фабрики для підтвердження реєстрації"""
        factory = RSVPConfirmedNotificationFactory()
        context = {
            'event': self.event,
            'participant': self.participant
        }
        
        notification = factory.create_notification(
            user=self.organizer,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.notification_type, Notification.RSVP_CONFIRMED)
        self.assertIn("participant", notification.message)
        self.assertIn("Test Event", notification.message)
        self.assertIn("зареєструвався", notification.message)
    
    def test_rsvp_cancelled_factory(self):
        """Тест фабрики для скасування реєстрації"""
        factory = RSVPCancelledNotificationFactory()
        context = {
            'event': self.event,
            'participant': self.participant
        }
        
        notification = factory.create_notification(
            user=self.organizer,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.notification_type, Notification.RSVP_CANCELLED)
        self.assertIn("participant", notification.message)
        self.assertIn("Test Event", notification.message)
        self.assertIn("скасував", notification.message)
    
    def test_factory_registry_get_factory(self):
        """Тест отримання фабрики з реєстру"""
        factory = NotificationFactoryRegistry.get_factory(Notification.EVENT_UPDATED)
        self.assertIsInstance(factory, EventUpdatedNotificationFactory)
        
        factory = NotificationFactoryRegistry.get_factory(Notification.RSVP_CONFIRMED)
        self.assertIsInstance(factory, RSVPConfirmedNotificationFactory)
    
    def test_factory_registry_unsupported_type(self):
        """Тест помилки для непідтримуваного типу"""
        with self.assertRaises(ValueError):
            NotificationFactoryRegistry.get_factory("unsupported_type")
    
    def test_factory_registry_create_notification(self):
        """Тест створення нотифікації через реєстр"""
        context = {
            'event': self.event,
            'participant': self.participant
        }
        
        notification = NotificationFactoryRegistry.create_notification(
            notification_type=Notification.RSVP_CONFIRMED,
            user=self.organizer,
            event=self.event,
            context=context
        )
        
        self.assertEqual(notification.user, self.organizer)
        self.assertEqual(notification.event, self.event)
        self.assertEqual(notification.notification_type, Notification.RSVP_CONFIRMED)
        self.assertIn("participant", notification.message)
    
    def test_factory_registry_register_new_factory(self):
        """Тест реєстрації нової фабрики"""
        class CustomNotificationFactory(EventUpdatedNotificationFactory):
            def get_notification_type(self):
                return "custom_type"
        
        custom_factory = CustomNotificationFactory()
        NotificationFactoryRegistry.register_factory("custom_type", custom_factory)
        
        retrieved_factory = NotificationFactoryRegistry.get_factory("custom_type")
        self.assertEqual(retrieved_factory, custom_factory)


class NotificationServiceIntegrationTests(TestCase):
    """Інтеграційні тести для NotificationService з Factory патерном"""
    
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant1 = User.objects.create_user(username="participant1", password="pass")
        self.participant2 = User.objects.create_user(username="participant2", password="pass")
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            location="Test Location",
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )
        
        # Створити RSVP для учасників
        RSVP.objects.create(user=self.participant1, event=self.event, status='going')
        RSVP.objects.create(user=self.participant2, event=self.event, status='going')
    
    def test_single_time_change_uses_specific_factory(self):
        """Тест використання EventTimeChangedNotificationFactory для одиночної зміни часу"""
        from notifications.services import NotificationService
        
        old_event_data = {
            'title': self.event.title,
            'description': self.event.description,
            'location': self.event.location,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
        }
        
        # Змінити тільки час
        self.event.starts_at = timezone.now() + timedelta(days=2)
        self.event.save()
        
        initial_count = Notification.objects.count()
        
        notifications_count = NotificationService.create_event_update_notification(
            self.event, old_event_data
        )
        
        # Перевірити, що створено 2 нотифікації (для 2 учасників)
        self.assertEqual(notifications_count, 2)
        self.assertEqual(Notification.objects.count(), initial_count + 2)
        
        # Перевірити, що використано правильний тип
        notifications = Notification.objects.filter(event=self.event).order_by('-created_at')[:2]
        for notification in notifications:
            self.assertEqual(notification.notification_type, Notification.EVENT_TIME_CHANGED)
            self.assertIn("змінено з", notification.message)
    
    def test_single_location_change_uses_specific_factory(self):
        """Тест використання EventLocationChangedNotificationFactory для одиночної зміни локації"""
        from notifications.services import NotificationService
        
        old_event_data = {
            'title': self.event.title,
            'description': self.event.description,
            'location': self.event.location,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
        }
        
        # Змінити тільки локацію
        self.event.location = "New Location"
        self.event.save()
        
        initial_count = Notification.objects.count()
        
        notifications_count = NotificationService.create_event_update_notification(
            self.event, old_event_data
        )
        
        # Перевірити, що створено 2 нотифікації
        self.assertEqual(notifications_count, 2)
        self.assertEqual(Notification.objects.count(), initial_count + 2)
        
        # Перевірити, що використано правильний тип
        notifications = Notification.objects.filter(event=self.event).order_by('-created_at')[:2]
        for notification in notifications:
            self.assertEqual(notification.notification_type, Notification.EVENT_LOCATION_CHANGED)
            self.assertIn("Test Location", notification.message)
            self.assertIn("New Location", notification.message)
    
    def test_multiple_changes_use_general_factory(self):
        """Тест використання EventUpdatedNotificationFactory для множинних змін"""
        from notifications.services import NotificationService
        
        old_event_data = {
            'title': self.event.title,
            'description': self.event.description,
            'location': self.event.location,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
        }
        
        # Змінити і час, і локацію
        self.event.starts_at = timezone.now() + timedelta(days=2)
        self.event.location = "New Location"
        self.event.save()
        
        initial_count = Notification.objects.count()
        
        notifications_count = NotificationService.create_event_update_notification(
            self.event, old_event_data
        )
        
        # Перевірити, що створено 2 нотифікації
        self.assertEqual(notifications_count, 2)
        self.assertEqual(Notification.objects.count(), initial_count + 2)
        
        # Перевірити, що використано загальний тип для комплексних змін
        notifications = Notification.objects.filter(event=self.event).order_by('-created_at')[:2]
        for notification in notifications:
            self.assertEqual(notification.notification_type, Notification.EVENT_UPDATED)
            self.assertIn("Час події змінено", notification.message)
            self.assertIn("Локацію змінено", notification.message)
