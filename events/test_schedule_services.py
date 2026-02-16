"""
Тести для DTO Pattern та PersonalScheduleService
"""
import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Event
from .schedule_services import ScheduleEntry, PersonalScheduleService
from tickets.models import RSVP

User = get_user_model()


class ScheduleEntryDTOTests(TestCase):
    """Тести для ScheduleEntry DTO"""

    def test_schedule_entry_creation(self):
        """Перевірка створення ScheduleEntry"""
        now = timezone.now()
        entry = ScheduleEntry(
            event_id=1,
            title="Test Event",
            starts_at=now,
            ends_at=now + timezone.timedelta(hours=2),
            status="published",
            location="Київ",
            description="Опис події",
            is_organizer=True,
            has_rsvp=False,
        )
        
        self.assertEqual(entry.event_id, 1)
        self.assertEqual(entry.title, "Test Event")
        self.assertEqual(entry.status, "published")
        self.assertTrue(entry.is_organizer)
        self.assertFalse(entry.has_rsvp)

    def test_schedule_entry_to_dict(self):
        """Перевірка конвертації ScheduleEntry в словник"""
        now = timezone.now()
        entry = ScheduleEntry(
            event_id=42,
            title="Conference",
            starts_at=now,
            ends_at=now + timezone.timedelta(hours=3),
            status="published",
            location="Львів",
            description="Annual conference",
            is_organizer=False,
            has_rsvp=True,
        )
        
        data = entry.to_dict()
        
        self.assertEqual(data["id"], 42)
        self.assertEqual(data["title"], "Conference")
        self.assertEqual(data["status"], "published")
        self.assertEqual(data["location"], "Львів")
        self.assertEqual(data["description"], "Annual conference")
        self.assertFalse(data["is_organizer"])
        self.assertTrue(data["has_rsvp"])
        self.assertIn("starts_at", data)
        self.assertIn("ends_at", data)

    def test_schedule_entry_to_dict_json_serializable(self):
        """Перевірка, що to_dict() повертає JSON-серіалізовані дані"""
        now = timezone.now()
        entry = ScheduleEntry(
            event_id=1,
            title="Test",
            starts_at=now,
            ends_at=now + timezone.timedelta(hours=1),
            status="draft",
            location="",
            description="",
            is_organizer=True,
            has_rsvp=False,
        )
        
        data = entry.to_dict()
        json_str = json.dumps(data)
        
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["id"], 1)


class PersonalScheduleServiceTests(TestCase):
    """Тести для PersonalScheduleService"""

    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant = User.objects.create_user(username="participant", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        
        self.organized_event = Event.objects.create(
            title="Organized Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
            location="Київ",
        )
        
        self.registered_event = Event.objects.create(
            title="Registered Event",
            starts_at=timezone.now() + timezone.timedelta(days=2),
            ends_at=timezone.now() + timezone.timedelta(days=2, hours=2),
            status=Event.PUBLISHED,
            organizer=self.other_user,
            location="Львів",
        )
        RSVP.objects.create(user=self.organizer, event=self.registered_event)
        
        self.draft_event = Event.objects.create(
            title="Draft Event",
            starts_at=timezone.now() + timezone.timedelta(days=3),
            ends_at=timezone.now() + timezone.timedelta(days=3, hours=2),
            status=Event.DRAFT,
            organizer=self.organizer,
        )
        
        self.unrelated_event = Event.objects.create(
            title="Unrelated Event",
            starts_at=timezone.now() + timezone.timedelta(days=4),
            ends_at=timezone.now() + timezone.timedelta(days=4, hours=2),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )


class GetUserEventsQuerysetTests(PersonalScheduleServiceTests):
    """Тести для get_user_events_queryset"""

    def test_returns_organized_events(self):
        """Повертає події, організовані користувачем"""
        qs = PersonalScheduleService.get_user_events_queryset(self.organizer)
        event_ids = list(qs.values_list("id", flat=True))
        
        self.assertIn(self.organized_event.id, event_ids)
        self.assertIn(self.draft_event.id, event_ids)

    def test_returns_registered_events(self):
        """Повертає події, на які користувач зареєстрований"""
        qs = PersonalScheduleService.get_user_events_queryset(self.organizer)
        event_ids = list(qs.values_list("id", flat=True))
        
        self.assertIn(self.registered_event.id, event_ids)

    def test_excludes_unrelated_events(self):
        """Не повертає події, до яких користувач не має відношення"""
        qs = PersonalScheduleService.get_user_events_queryset(self.organizer)
        event_ids = list(qs.values_list("id", flat=True))
        
        self.assertNotIn(self.unrelated_event.id, event_ids)

    def test_ordered_by_starts_at(self):
        """Результати відсортовані за датою початку"""
        qs = PersonalScheduleService.get_user_events_queryset(self.organizer)
        events = list(qs)
        
        for i in range(len(events) - 1):
            self.assertLessEqual(events[i].starts_at, events[i + 1].starts_at)


class GetUserRsvpEventIdsTests(PersonalScheduleServiceTests):
    """Тести для get_user_rsvp_event_ids"""

    def test_returns_rsvp_event_ids(self):
        """Повертає ID подій з RSVP користувача"""
        ids = PersonalScheduleService.get_user_rsvp_event_ids(self.organizer)
        
        self.assertIn(self.registered_event.id, ids)

    def test_returns_set(self):
        """Повертає множину (set)"""
        ids = PersonalScheduleService.get_user_rsvp_event_ids(self.organizer)
        
        self.assertIsInstance(ids, set)

    def test_empty_for_user_without_rsvps(self):
        """Порожня множина для користувача без RSVP"""
        new_user = User.objects.create_user(username="newuser", password="pass")
        ids = PersonalScheduleService.get_user_rsvp_event_ids(new_user)
        
        self.assertEqual(ids, set())


class GetUserScheduleEntriesTests(PersonalScheduleServiceTests):
    """Тести для get_user_schedule_entries"""

    def test_returns_schedule_entries(self):
        """Повертає список ScheduleEntry"""
        entries = PersonalScheduleService.get_user_schedule_entries(self.organizer)
        
        self.assertIsInstance(entries, list)
        self.assertTrue(all(isinstance(e, ScheduleEntry) for e in entries))

    def test_marks_organizer_correctly(self):
        """Правильно позначає is_organizer"""
        entries = PersonalScheduleService.get_user_schedule_entries(self.organizer)
        
        organized_entry = next(e for e in entries if e.event_id == self.organized_event.id)
        registered_entry = next(e for e in entries if e.event_id == self.registered_event.id)
        
        self.assertTrue(organized_entry.is_organizer)
        self.assertFalse(registered_entry.is_organizer)

    def test_marks_rsvp_correctly(self):
        """Правильно позначає has_rsvp"""
        entries = PersonalScheduleService.get_user_schedule_entries(self.organizer)
        
        organized_entry = next(e for e in entries if e.event_id == self.organized_event.id)
        registered_entry = next(e for e in entries if e.event_id == self.registered_event.id)
        
        self.assertFalse(organized_entry.has_rsvp)
        self.assertTrue(registered_entry.has_rsvp)

    def test_no_n_plus_one_queries(self):
        """Перевірка відсутності N+1 проблеми"""
        for i in range(5):
            event = Event.objects.create(
                title=f"Extra Event {i}",
                starts_at=timezone.now() + timezone.timedelta(days=10 + i),
                ends_at=timezone.now() + timezone.timedelta(days=10 + i, hours=2),
                status=Event.PUBLISHED,
                organizer=self.other_user,
            )
            RSVP.objects.create(user=self.organizer, event=event)
        
        with self.assertNumQueries(2):
            entries = PersonalScheduleService.get_user_schedule_entries(self.organizer)
            _ = len(entries)


class GetScheduleJsonDataTests(PersonalScheduleServiceTests):
    """Тести для get_schedule_json_data"""

    def test_returns_valid_json(self):
        """Повертає валідний JSON"""
        json_data = PersonalScheduleService.get_schedule_json_data(self.organizer)
        
        self.assertIsInstance(json_data, str)
        parsed = json.loads(json_data)
        self.assertIsInstance(parsed, list)

    def test_json_contains_event_data(self):
        """JSON містить дані про події"""
        json_data = PersonalScheduleService.get_schedule_json_data(self.organizer)
        parsed = json.loads(json_data)
        
        event_ids = [e["id"] for e in parsed]
        self.assertIn(self.organized_event.id, event_ids)
        self.assertIn(self.registered_event.id, event_ids)

    def test_json_structure(self):
        """Перевірка структури JSON"""
        json_data = PersonalScheduleService.get_schedule_json_data(self.organizer)
        parsed = json.loads(json_data)
        
        if parsed:
            event = parsed[0]
            required_keys = ["id", "title", "starts_at", "ends_at", "status", 
                           "location", "description", "is_organizer", "has_rsvp"]
            for key in required_keys:
                self.assertIn(key, event)


# ============================================================================
# Тести для Decorator Pattern (обгортки розкладу)
# ============================================================================

from .schedule_services import (
    BaseScheduleProvider,
    FilteredScheduleDecorator,
    HighlightedScheduleDecorator,
)
from datetime import timedelta


class BaseScheduleProviderTests(PersonalScheduleServiceTests):
    """Тести для BaseScheduleProvider"""

    def test_returns_same_entries_as_service(self):
        """BaseScheduleProvider повертає ті самі entries, що PersonalScheduleService"""
        provider = BaseScheduleProvider()
        provider_entries = provider.get_entries(self.organizer)
        service_entries = PersonalScheduleService.get_user_schedule_entries(self.organizer)
        
        self.assertEqual(len(provider_entries), len(service_entries))
        
        provider_ids = {e.event_id for e in provider_entries}
        service_ids = {e.event_id for e in service_entries}
        self.assertEqual(provider_ids, service_ids)

    def test_returns_schedule_entry_list(self):
        """Повертає список ScheduleEntry"""
        provider = BaseScheduleProvider()
        entries = provider.get_entries(self.organizer)
        
        self.assertIsInstance(entries, list)
        self.assertTrue(all(isinstance(e, ScheduleEntry) for e in entries))


class FilteredScheduleDecoratorTests(PersonalScheduleServiceTests):
    """Тести для FilteredScheduleDecorator"""

    def setUp(self):
        super().setUp()
        self.past_event = Event.objects.create(
            title="Past Event",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=timezone.now() - timedelta(days=1) + timedelta(hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )

    def test_only_upcoming_filters_past_events(self):
        """only_upcoming відсікає минулі події"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(provider, only_upcoming=True)
        
        entries = filtered.get_entries(self.organizer)
        event_ids = {e.event_id for e in entries}
        
        self.assertNotIn(self.past_event.id, event_ids)
        self.assertIn(self.organized_event.id, event_ids)

    def test_only_organizer_filters_non_organizer_events(self):
        """only_organizer лишає тільки події, де is_organizer=True"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(provider, only_organizer=True)
        
        entries = filtered.get_entries(self.organizer)
        
        self.assertTrue(all(e.is_organizer for e in entries))
        event_ids = {e.event_id for e in entries}
        self.assertIn(self.organized_event.id, event_ids)
        self.assertNotIn(self.registered_event.id, event_ids)

    def test_only_published_filters_non_published(self):
        """only_published лишає тільки status=published"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(provider, only_published=True)
        
        entries = filtered.get_entries(self.organizer)
        
        self.assertTrue(all(e.status == "published" for e in entries))
        event_ids = {e.event_id for e in entries}
        self.assertNotIn(self.draft_event.id, event_ids)

    def test_no_filter_returns_all(self):
        """Без фільтрів повертає всі записи"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(provider)
        
        filtered_entries = filtered.get_entries(self.organizer)
        base_entries = provider.get_entries(self.organizer)
        
        self.assertEqual(len(filtered_entries), len(base_entries))

    def test_combined_filters(self):
        """Комбінація фільтрів працює"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(
            provider, 
            only_upcoming=True, 
            only_organizer=True
        )
        
        entries = filtered.get_entries(self.organizer)
        
        now = timezone.now()
        for entry in entries:
            self.assertTrue(entry.is_organizer)
            self.assertGreater(entry.starts_at, now)


class HighlightedScheduleDecoratorTests(PersonalScheduleServiceTests):
    """Тести для HighlightedScheduleDecorator"""

    def setUp(self):
        super().setUp()
        self.soon_event = Event.objects.create(
            title="Soon Event",
            starts_at=timezone.now() + timedelta(hours=12),
            ends_at=timezone.now() + timedelta(hours=14),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )

    def test_highlight_soon_marks_upcoming_24h(self):
        """soon підсвічує події в межах 24 годин"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="soon")
        
        entries = highlighted.get_entries(self.organizer)
        soon_entry = next((e for e in entries if e.event_id == self.soon_event.id), None)
        
        self.assertIsNotNone(soon_entry)
        self.assertEqual(soon_entry.highlight_reason, "soon")

    def test_highlight_soon_not_marks_far_events(self):
        """soon не підсвічує події далі 24 годин"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="soon")
        
        entries = highlighted.get_entries(self.organizer)
        # registered_event через 2 дні - точно далі 24 годин
        far_entry = next((e for e in entries if e.event_id == self.registered_event.id), None)
        
        self.assertIsNotNone(far_entry)
        self.assertEqual(far_entry.highlight_reason, "")

    def test_highlight_organizer_marks_organizer_events(self):
        """organizer підсвічує події організатора"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="organizer")
        
        entries = highlighted.get_entries(self.organizer)
        organized_entry = next((e for e in entries if e.event_id == self.organized_event.id), None)
        registered_entry = next((e for e in entries if e.event_id == self.registered_event.id), None)
        
        self.assertEqual(organized_entry.highlight_reason, "organizer")
        self.assertEqual(registered_entry.highlight_reason, "")

    def test_no_highlight_mode_returns_unchanged(self):
        """Без режиму підсвічування entries не змінюються"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="")
        
        entries = highlighted.get_entries(self.organizer)
        
        for entry in entries:
            self.assertEqual(entry.highlight_reason, "")

    def test_highlight_does_not_break_entries(self):
        """Підсвічування не ламає entries"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="soon")
        
        entries = highlighted.get_entries(self.organizer)
        
        self.assertIsInstance(entries, list)
        self.assertTrue(all(isinstance(e, ScheduleEntry) for e in entries))

    def test_highlight_popular_marks_events_with_5_plus_rsvps(self):
        """popular підсвічує події з 5+ RSVP"""
        from tickets.models import RSVP
        
        # Створюємо подію з 5 RSVP
        popular_event = Event.objects.create(
            title="Popular Event",
            starts_at=timezone.now() + timedelta(days=5),
            ends_at=timezone.now() + timedelta(days=5, hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )
        
        # Додаємо 5 RSVP від різних користувачів
        for i in range(5):
            user = User.objects.create_user(username=f"rsvp_user_{i}", password="pass")
            RSVP.objects.create(user=user, event=popular_event, status="going")
        
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="popular")
        
        entries = highlighted.get_entries(self.organizer)
        popular_entry = next((e for e in entries if e.event_id == popular_event.id), None)
        
        self.assertIsNotNone(popular_entry)
        self.assertEqual(popular_entry.highlight_reason, "popular")

    def test_highlight_popular_not_marks_events_with_less_than_5_rsvps(self):
        """popular не підсвічує події з менше ніж 5 RSVP"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="popular")
        
        entries = highlighted.get_entries(self.organizer)
        
        # organized_event та registered_event мають менше 5 RSVP
        for entry in entries:
            if entry.event_id in [self.organized_event.id, self.registered_event.id]:
                self.assertEqual(entry.highlight_reason, "")


class DecoratorChainTests(PersonalScheduleServiceTests):
    """Тести для ланцюжка декораторів"""

    def setUp(self):
        super().setUp()
        self.soon_event = Event.objects.create(
            title="Soon Organized Event",
            starts_at=timezone.now() + timedelta(hours=6),
            ends_at=timezone.now() + timedelta(hours=8),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )

    def test_filter_then_highlight(self):
        """Фільтрація потім підсвічування працює"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(provider, only_organizer=True)
        highlighted = HighlightedScheduleDecorator(filtered, highlight_mode="soon")
        
        entries = highlighted.get_entries(self.organizer)
        
        self.assertTrue(all(e.is_organizer for e in entries))
        
        soon_entry = next((e for e in entries if e.event_id == self.soon_event.id), None)
        if soon_entry:
            self.assertEqual(soon_entry.highlight_reason, "soon")

    def test_highlight_then_filter(self):
        """Підсвічування потім фільтрація працює"""
        provider = BaseScheduleProvider()
        highlighted = HighlightedScheduleDecorator(provider, highlight_mode="organizer")
        filtered = FilteredScheduleDecorator(highlighted, only_upcoming=True)
        
        entries = filtered.get_entries(self.organizer)
        
        now = timezone.now()
        for entry in entries:
            self.assertGreater(entry.starts_at, now)

    def test_multiple_decorators_chain(self):
        """Множинний ланцюжок декораторів"""
        provider = BaseScheduleProvider()
        filtered = FilteredScheduleDecorator(provider, only_upcoming=True, only_published=True)
        highlighted = HighlightedScheduleDecorator(filtered, highlight_mode="organizer")
        
        entries = highlighted.get_entries(self.organizer)
        
        now = timezone.now()
        for entry in entries:
            self.assertGreater(entry.starts_at, now)
            self.assertEqual(entry.status, "published")
