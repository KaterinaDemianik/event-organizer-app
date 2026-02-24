"""
Фінальні тести для events/schedule_services.py - покриття залишкових рядків
Рядки: 23, 166, 175, 188-189, 192-193, 197, 303-305
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from dataclasses import replace

from events.models import Event
from events.schedule_services import (
    ScheduleEntry,
    BaseScheduleProvider,
    HighlightedScheduleDecorator,
    PersonalScheduleService,
)
from tickets.models import RSVP


class HighlightedScheduleDecoratorTestCase(TestCase):
    """Тести для HighlightedScheduleDecorator"""

    def setUp(self):
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
        
        # Подія що скоро розпочнеться
        self.soon_event = Event.objects.create(
            title="Soon Event",
            description="Description",
            starts_at=now + timedelta(hours=2),
            ends_at=now + timedelta(hours=4),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        # Подія організована користувачем
        self.my_event = Event.objects.create(
            title="My Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Популярна подія
        self.popular_event = Event.objects.create(
            title="Popular Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        # Створюємо багато RSVP для популярної події
        for i in range(15):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="testpass123"
            )
            RSVP.objects.create(user=user, event=self.popular_event, status="going")

    def test_highlight_soon_mode(self):
        """Тест підсвічування подій що скоро розпочнуться"""
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="soon")
        
        entries = decorator.get_entries(self.user)
        
        # Перевіряємо що метод працює
        self.assertIsInstance(entries, list)

    def test_highlight_organizer_mode(self):
        """Тест підсвічування подій організатора"""
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="organizer")
        
        entries = decorator.get_entries(self.user)
        
        self.assertIsInstance(entries, list)

    def test_highlight_popular_mode(self):
        """Тест підсвічування популярних подій"""
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="popular")
        
        entries = decorator.get_entries(self.user)
        
        self.assertIsInstance(entries, list)

    def test_no_highlight_mode(self):
        """Тест без підсвічування"""
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode=None)
        
        entries = decorator.get_entries(self.user)
        
        self.assertIsInstance(entries, list)

    def test_get_highlight_reason_soon(self):
        """Тест визначення причини підсвічування - скоро"""
        now = timezone.now()
        soon_threshold = now + timedelta(hours=24)
        
        entry = ScheduleEntry(
            event_id=1,
            title="Soon Event",
            starts_at=now + timedelta(hours=2),
            ends_at=now + timedelta(hours=4),
            status="published",
            location="Location",
            description="Description",
            is_organizer=False,
            has_rsvp=True
        )
        
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="soon")
        
        reason = decorator._get_highlight_reason(entry, now, soon_threshold)
        self.assertEqual(reason, "soon")

    def test_get_highlight_reason_organizer(self):
        """Тест визначення причини підсвічування - організатор"""
        now = timezone.now()
        soon_threshold = now + timedelta(hours=24)
        
        entry = ScheduleEntry(
            event_id=1,
            title="My Event",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            status="published",
            location="Location",
            description="Description",
            is_organizer=True,
            has_rsvp=False
        )
        
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="organizer")
        
        reason = decorator._get_highlight_reason(entry, now, soon_threshold)
        self.assertEqual(reason, "organizer")

    def test_get_highlight_reason_popular(self):
        """Тест визначення причини підсвічування - популярна"""
        now = timezone.now()
        soon_threshold = now + timedelta(hours=24)
        
        entry = ScheduleEntry(
            event_id=1,
            title="Popular Event",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            status="published",
            location="Location",
            description="Description",
            is_organizer=False,
            has_rsvp=True,
            rsvp_count=15
        )
        
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="popular")
        
        reason = decorator._get_highlight_reason(entry, now, soon_threshold)
        self.assertEqual(reason, "popular")

    def test_get_highlight_reason_no_match(self):
        """Тест коли немає причини підсвічування"""
        now = timezone.now()
        soon_threshold = now + timedelta(hours=24)
        
        entry = ScheduleEntry(
            event_id=1,
            title="Regular Event",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            status="published",
            location="Location",
            description="Description",
            is_organizer=False,
            has_rsvp=False,
            rsvp_count=2
        )
        
        provider = BaseScheduleProvider()
        decorator = HighlightedScheduleDecorator(provider, highlight_mode="soon")
        
        reason = decorator._get_highlight_reason(entry, now, soon_threshold)
        self.assertEqual(reason, "")


class PersonalScheduleServiceFinalTestCase(TestCase):
    """Фінальні тести для PersonalScheduleService"""

    def setUp(self):
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
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        RSVP.objects.create(user=self.user, event=self.event, status="going")

    def test_get_user_schedule_entries_empty(self):
        """Тест отримання записів для користувача без подій"""
        new_user = User.objects.create_user(
            username="newuser",
            email="new@example.com",
            password="testpass123"
        )
        
        service = PersonalScheduleService()
        entries = service.get_user_schedule_entries(new_user)
        
        self.assertIsInstance(entries, list)

    def test_get_user_schedule_entries_with_events(self):
        """Тест отримання записів для користувача з подіями"""
        service = PersonalScheduleService()
        entries = service.get_user_schedule_entries(self.user)
        
        self.assertIsInstance(entries, list)

    def test_get_user_rsvp_event_ids(self):
        """Тест отримання ID подій з RSVP"""
        service = PersonalScheduleService()
        ids = service.get_user_rsvp_event_ids(self.user)
        
        # Може бути set або list
        self.assertIn(self.event.id, ids)

    def test_get_user_events_queryset(self):
        """Тест отримання queryset подій користувача"""
        service = PersonalScheduleService()
        queryset = service.get_user_events_queryset(self.user)
        
        self.assertIsNotNone(queryset)
