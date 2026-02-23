"""
Тести для events/services.py - покриття RSVPService та EventArchiveService
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.services import SingletonMeta, EventArchiveService, RSVPService
from tickets.models import RSVP


class SingletonMetaTestCase(TestCase):
    """Тести для SingletonMeta метакласу"""

    def test_singleton_returns_same_instance(self):
        """Тест що Singleton повертає той самий екземпляр"""
        instance1 = EventArchiveService()
        instance2 = EventArchiveService()
        self.assertIs(instance1, instance2)


class EventArchiveServiceTestCase(TestCase):
    """Тести для EventArchiveService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Завершена опублікована подія
        self.past_published = Event.objects.create(
            title="Past Published",
            description="Description",
            starts_at=now - timedelta(days=3),
            ends_at=now - timedelta(days=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Майбутня опублікована подія
        self.future_published = Event.objects.create(
            title="Future Published",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Завершена чернетка
        self.past_draft = Event.objects.create(
            title="Past Draft",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.user,
            status=Event.DRAFT
        )
        
        self.service = EventArchiveService()

    def test_archive_past_events_archives_completed(self):
        """Тест що archive_past_events архівує завершені опубліковані події"""
        count = self.service.archive_past_events()
        
        self.assertEqual(count, 1)
        
        self.past_published.refresh_from_db()
        self.assertEqual(self.past_published.status, Event.ARCHIVED)

    def test_archive_past_events_ignores_future(self):
        """Тест що archive_past_events не чіпає майбутні події"""
        self.service.archive_past_events()
        
        self.future_published.refresh_from_db()
        self.assertEqual(self.future_published.status, Event.PUBLISHED)

    def test_archive_past_events_ignores_drafts(self):
        """Тест що archive_past_events не чіпає чернетки"""
        self.service.archive_past_events()
        
        self.past_draft.refresh_from_db()
        self.assertEqual(self.past_draft.status, Event.DRAFT)

    def test_archive_past_events_returns_zero_when_none(self):
        """Тест що archive_past_events повертає 0 коли немає подій для архівування"""
        # Архівуємо всі
        self.service.archive_past_events()
        
        # Повторний виклик має повернути 0
        count = self.service.archive_past_events()
        self.assertEqual(count, 0)

    def test_archive_event_success(self):
        """Тест успішного архівування окремої події"""
        success, error = self.service.archive_event(self.past_published)
        
        self.assertTrue(success)
        self.assertIsNone(error)
        
        self.past_published.refresh_from_db()
        self.assertEqual(self.past_published.status, Event.ARCHIVED)

    def test_archive_event_future_fails(self):
        """Тест що не можна архівувати майбутню подію"""
        success, error = self.service.archive_event(self.future_published)
        
        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn("завершені", error)

    def test_archive_event_draft_fails(self):
        """Тест що не можна архівувати чернетку"""
        success, error = self.service.archive_event(self.past_draft)
        
        self.assertFalse(success)
        self.assertIsNotNone(error)


class RSVPServiceTestCase(TestCase):
    """Тести для RSVPService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123"
        )
        
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Майбутня опублікована подія
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED,
            capacity=10
        )
        
        # Подія що вже розпочалась
        self.started_event = Event.objects.create(
            title="Started Event",
            description="Description",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=1),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        # Чернетка
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )
        
        # Скасована подія
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=2),
            organizer=self.organizer,
            status=Event.CANCELLED
        )
        
        # Архівована подія
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.organizer,
            status=Event.ARCHIVED
        )
        
        # Подія з конфліктом часу
        self.conflicting_event = Event.objects.create(
            title="Conflicting Event",
            description="Description",
            starts_at=now + timedelta(days=1, hours=1),
            ends_at=now + timedelta(days=1, hours=3),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_get_conflicting_events_no_conflicts(self):
        """Тест коли немає конфліктів"""
        conflicts = RSVPService.get_conflicting_events(self.user, self.future_event)
        self.assertEqual(conflicts, [])

    def test_get_conflicting_events_with_conflict(self):
        """Тест коли є конфлікт часу"""
        # Реєструємо на подію що перетинається
        RSVP.objects.create(user=self.user, event=self.conflicting_event, status="going")
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.future_event)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0], self.conflicting_event)

    def test_get_conflicting_events_excludes_same_event(self):
        """Тест що та ж подія не вважається конфліктом"""
        RSVP.objects.create(user=self.user, event=self.future_event, status="going")
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.future_event)
        self.assertEqual(conflicts, [])

    def test_check_time_conflict_no_conflict(self):
        """Тест check_time_conflict коли немає конфлікту"""
        has_conflict, conflicting_event = RSVPService.check_time_conflict(self.user, self.future_event)
        
        self.assertFalse(has_conflict)
        self.assertIsNone(conflicting_event)

    def test_check_time_conflict_with_conflict(self):
        """Тест check_time_conflict коли є конфлікт"""
        RSVP.objects.create(user=self.user, event=self.conflicting_event, status="going")
        
        has_conflict, conflicting_event = RSVPService.check_time_conflict(self.user, self.future_event)
        
        self.assertTrue(has_conflict)
        self.assertEqual(conflicting_event, self.conflicting_event)

    def test_can_create_rsvp_success(self):
        """Тест успішної перевірки можливості створення RSVP"""
        can_create, error = RSVPService.can_create_rsvp(self.user, self.future_event)
        
        self.assertTrue(can_create)
        self.assertIsNone(error)

    def test_can_create_rsvp_draft_event(self):
        """Тест що не можна реєструватися на чернетку"""
        can_create, error = RSVPService.can_create_rsvp(self.user, self.draft_event)
        
        self.assertFalse(can_create)
        self.assertIn("не опублікована", error)

    def test_can_create_rsvp_cancelled_event(self):
        """Тест що не можна реєструватися на скасовану подію"""
        can_create, error = RSVPService.can_create_rsvp(self.user, self.cancelled_event)
        
        self.assertFalse(can_create)
        self.assertIn("скасовано", error)

    def test_can_create_rsvp_archived_event(self):
        """Тест що не можна реєструватися на архівовану подію"""
        can_create, error = RSVPService.can_create_rsvp(self.user, self.archived_event)
        
        self.assertFalse(can_create)
        self.assertIn("архівована", error)

    def test_can_create_rsvp_started_event(self):
        """Тест що не можна реєструватися на подію що вже розпочалась"""
        can_create, error = RSVPService.can_create_rsvp(self.user, self.started_event)
        
        self.assertFalse(can_create)
        self.assertIn("розпочалась", error)

    def test_can_create_rsvp_already_registered(self):
        """Тест що не можна реєструватися повторно"""
        RSVP.objects.create(user=self.user, event=self.future_event, status="going")
        
        can_create, error = RSVPService.can_create_rsvp(self.user, self.future_event)
        
        self.assertFalse(can_create)
        self.assertIn("вже зареєстровані", error)

    def test_can_create_rsvp_capacity_full(self):
        """Тест що не можна реєструватися коли місця закінчились"""
        # Створюємо подію з місткістю 1
        limited_event = Event.objects.create(
            title="Limited Event",
            description="Description",
            starts_at=timezone.now() + timedelta(days=5),
            ends_at=timezone.now() + timedelta(days=5, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED,
            capacity=1
        )
        
        # Реєструємо першого користувача
        RSVP.objects.create(user=self.user, event=limited_event, status="going")
        
        # Другий користувач не може зареєструватися
        can_create, error = RSVPService.can_create_rsvp(self.user2, limited_event)
        
        self.assertFalse(can_create)
        self.assertIn("місця зайняті", error)

    def test_can_create_rsvp_time_conflict(self):
        """Тест що не можна реєструватися при конфлікті часу"""
        RSVP.objects.create(user=self.user, event=self.conflicting_event, status="going")
        
        can_create, error = RSVPService.can_create_rsvp(self.user, self.future_event)
        
        self.assertFalse(can_create)
        self.assertIn("Конфлікт часу", error)

    def test_can_create_rsvp_unlimited_capacity(self):
        """Тест реєстрації на подію без обмеження місткості"""
        unlimited_event = Event.objects.create(
            title="Unlimited Event",
            description="Description",
            starts_at=timezone.now() + timedelta(days=6),
            ends_at=timezone.now() + timedelta(days=6, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED,
            capacity=None
        )
        
        can_create, error = RSVPService.can_create_rsvp(self.user, unlimited_event)
        
        self.assertTrue(can_create)
        self.assertIsNone(error)
