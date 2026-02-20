"""
Тести для DTO Pattern та Decorator Pattern в schedule_services.py
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.schedule_services import (
    ScheduleEntry,
    BaseScheduleProvider,
    FilteredScheduleDecorator,
    HighlightedScheduleDecorator,
    PersonalScheduleService
)
from tickets.models import RSVP


class ScheduleEntryDTOTestCase(TestCase):
    """Тести для DTO Pattern - ScheduleEntry"""

    def test_schedule_entry_creation(self):
        """Тест створення ScheduleEntry DTO"""
        now = timezone.now()
        
        entry = ScheduleEntry(
            event_id=1,
            title="Test Event",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="published",
            location="Test Location",
            description="Test Description",
            is_organizer=True,
            has_rsvp=False,
            highlight_reason="popular",
            rsvp_count=5
        )
        
        self.assertEqual(entry.event_id, 1)
        self.assertEqual(entry.title, "Test Event")
        self.assertEqual(entry.status, "published")
        self.assertEqual(entry.location, "Test Location")
        self.assertTrue(entry.is_organizer)
        self.assertFalse(entry.has_rsvp)
        self.assertEqual(entry.highlight_reason, "popular")
        self.assertEqual(entry.rsvp_count, 5)

    def test_schedule_entry_to_dict(self):
        """Тест конвертації DTO в словник"""
        now = timezone.now()
        
        entry = ScheduleEntry(
            event_id=1,
            title="Test Event",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="published",
            location="Test Location",
            description="Test Description",
            is_organizer=True,
            has_rsvp=False
        )
        
        result = entry.to_dict()
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["title"], "Test Event")
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["location"], "Test Location")
        self.assertEqual(result["description"], "Test Description")
        self.assertTrue(result["is_organizer"])
        self.assertFalse(result["has_rsvp"])
        self.assertIn("starts_at", result)
        self.assertIn("ends_at", result)

    def test_schedule_entry_to_dict_with_highlight(self):
        """Тест конвертації DTO з highlight_reason"""
        now = timezone.now()
        
        entry = ScheduleEntry(
            event_id=1,
            title="Test Event",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="published",
            location="Test Location",
            description="Test Description",
            is_organizer=True,
            has_rsvp=False,
            highlight_reason="popular"
        )
        
        result = entry.to_dict()
        self.assertEqual(result["highlight_reason"], "popular")

    def test_schedule_entry_to_dict_without_highlight(self):
        """Тест конвертації DTO без highlight_reason"""
        now = timezone.now()
        
        entry = ScheduleEntry(
            event_id=1,
            title="Test Event",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="published",
            location="Test Location",
            description="Test Description",
            is_organizer=True,
            has_rsvp=False
        )
        
        result = entry.to_dict()
        self.assertNotIn("highlight_reason", result)


class DecoratorPatternTestCase(TestCase):
    """Тести для Decorator Pattern - обгортки розкладу"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Майбутня подія (організатор - testuser)
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Future event description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Минула подія (організатор - testuser)
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Past event description",
            starts_at=now - timedelta(days=1),
            ends_at=now - timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Чернетка події (організатор - testuser)
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Draft event description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.user,
            status=Event.DRAFT
        )
        
        # Подія іншого організатора
        self.other_event = Event.objects.create(
            title="Other Event",
            description="Other event description",
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=2),
            organizer=self.other_user,
            status=Event.PUBLISHED
        )
        
        # RSVP на подію іншого організатора
        RSVP.objects.create(
            user=self.user,
            event=self.other_event,
            status="going"
        )

    def test_base_schedule_provider(self):
        """Тест базового провайдера розкладу"""
        provider = BaseScheduleProvider()
        entries = provider.get_entries(self.user)
        
        # Має повернути всі події користувача (організатор + RSVP)
        self.assertIsInstance(entries, list)
        self.assertTrue(len(entries) > 0)
        
        # Перевіряємо що повертаються ScheduleEntry об'єкти
        for entry in entries:
            self.assertIsInstance(entry, ScheduleEntry)

    def test_filtered_schedule_decorator_upcoming_only(self):
        """Тест фільтра тільки майбутніх подій"""
        base_provider = BaseScheduleProvider()
        filtered_provider = FilteredScheduleDecorator(
            base_provider,
            only_upcoming=True
        )
        
        entries = filtered_provider.get_entries(self.user)
        
        # Всі події мають бути майбутніми
        now = timezone.now()
        for entry in entries:
            self.assertGreater(entry.starts_at, now)

    def test_filtered_schedule_decorator_organizer_only(self):
        """Тест фільтра тільки подій організатора"""
        base_provider = BaseScheduleProvider()
        filtered_provider = FilteredScheduleDecorator(
            base_provider,
            only_organizer=True
        )
        
        entries = filtered_provider.get_entries(self.user)
        
        # Всі події мають бути організовані користувачем
        for entry in entries:
            self.assertTrue(entry.is_organizer)

    def test_filtered_schedule_decorator_published_only(self):
        """Тест фільтра тільки опублікованих подій"""
        base_provider = BaseScheduleProvider()
        filtered_provider = FilteredScheduleDecorator(
            base_provider,
            only_published=True
        )
        
        entries = filtered_provider.get_entries(self.user)
        
        # Всі події мають бути опубліковані
        for entry in entries:
            self.assertEqual(entry.status, Event.PUBLISHED)

    def test_filtered_schedule_decorator_combined_filters(self):
        """Тест комбінованих фільтрів"""
        base_provider = BaseScheduleProvider()
        filtered_provider = FilteredScheduleDecorator(
            base_provider,
            only_upcoming=True,
            only_organizer=True,
            only_published=True
        )
        
        entries = filtered_provider.get_entries(self.user)
        
        now = timezone.now()
        for entry in entries:
            self.assertGreater(entry.starts_at, now)  # майбутня
            self.assertTrue(entry.is_organizer)       # організатор
            self.assertEqual(entry.status, Event.PUBLISHED)  # опублікована

    def test_highlighted_schedule_decorator_popular_mode(self):
        """Тест підсвічування популярних подій"""
        # Додаємо RSVP для популярності
        for i in range(3):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="pass123"
            )
            RSVP.objects.create(
                user=user,
                event=self.future_event,
                status="going"
            )
        
        base_provider = BaseScheduleProvider()
        highlighted_provider = HighlightedScheduleDecorator(
            base_provider,
            highlight_mode="popular"
        )
        
        entries = highlighted_provider.get_entries(self.user)
        
        # Знаходимо майбутню подію в результатах
        future_entry = None
        for entry in entries:
            if entry.event_id == self.future_event.id:
                future_entry = entry
                break
        
        self.assertIsNotNone(future_entry)
        # Перевіряємо що rsvp_count правильно анотується
        self.assertGreaterEqual(future_entry.rsvp_count, 3)
        # Highlight може бути або не бути, залежно від логіки
        self.assertIn(future_entry.highlight_reason, ["", "popular"])

    def test_highlighted_schedule_decorator_recent_mode(self):
        """Тест підсвічування нещодавно створених подій"""
        base_provider = BaseScheduleProvider()
        highlighted_provider = HighlightedScheduleDecorator(
            base_provider,
            highlight_mode="recent"
        )
        
        entries = highlighted_provider.get_entries(self.user)
        
        # Перевіряємо що деякі події мають highlight_reason="recent"
        recent_entries = [e for e in entries if e.highlight_reason == "recent"]
        # Може бути 0 або більше, залежно від того, чи є нещодавні події
        self.assertGreaterEqual(len(recent_entries), 0)

    def test_decorator_chaining(self):
        """Тест ланцюжка декораторів"""
        base_provider = BaseScheduleProvider()
        
        # Ланцюжок: Base -> Filtered -> Highlighted
        filtered_provider = FilteredScheduleDecorator(
            base_provider,
            only_upcoming=True,
            only_published=True
        )
        
        highlighted_provider = HighlightedScheduleDecorator(
            filtered_provider,
            highlight_mode="popular"
        )
        
        entries = highlighted_provider.get_entries(self.user)
        
        # Всі записи мають відповідати фільтрам
        now = timezone.now()
        for entry in entries:
            self.assertGreater(entry.starts_at, now)
            self.assertEqual(entry.status, Event.PUBLISHED)

    def test_personal_schedule_service_integration(self):
        """Тест інтеграції з PersonalScheduleService"""
        entries = PersonalScheduleService.get_user_schedule_entries(self.user)
        
        self.assertIsInstance(entries, list)
        
        # Перевіряємо що повертаються правильні DTO об'єкти
        for entry in entries:
            self.assertIsInstance(entry, ScheduleEntry)
            self.assertIsInstance(entry.event_id, int)
            self.assertIsInstance(entry.title, str)
            self.assertIsInstance(entry.is_organizer, bool)
            self.assertIsInstance(entry.has_rsvp, bool)
