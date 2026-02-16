"""
Тести для RSVPService - перевірка конфлікту часу RSVP
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Event
from .services import RSVPService
from tickets.models import RSVP

User = get_user_model()


class RSVPServiceBaseTests(TestCase):
    """Базовий клас для тестів RSVPService"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        
        # Базова подія: завтра 10:00-12:00
        self.base_event = Event.objects.create(
            title="Base Event",
            starts_at=timezone.now() + timedelta(days=1, hours=10),
            ends_at=timezone.now() + timedelta(days=1, hours=12),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )


class GetConflictingEventsTests(RSVPServiceBaseTests):
    """Тести для get_conflicting_events"""

    def test_no_conflicts_when_no_rsvps(self):
        """Немає конфліктів, якщо користувач не має RSVP"""
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(conflicts, [])

    def test_no_conflict_when_events_dont_overlap(self):
        """Немає конфлікту, якщо події не перетинаються"""
        # Подія 14:00-16:00 (після base_event)
        non_overlapping = Event.objects.create(
            title="Non-overlapping Event",
            starts_at=timezone.now() + timedelta(days=1, hours=14),
            ends_at=timezone.now() + timedelta(days=1, hours=16),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=non_overlapping)
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(conflicts, [])

    def test_conflict_when_events_overlap(self):
        """Є конфлікт, якщо події перетинаються"""
        # Подія 11:00-13:00 (перетинається з base_event 10:00-12:00)
        overlapping = Event.objects.create(
            title="Overlapping Event",
            starts_at=timezone.now() + timedelta(days=1, hours=11),
            ends_at=timezone.now() + timedelta(days=1, hours=13),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=overlapping)
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].id, overlapping.id)

    def test_conflict_when_event_contains_another(self):
        """Є конфлікт, якщо одна подія повністю містить іншу"""
        # Подія 9:00-14:00 (містить base_event 10:00-12:00)
        containing = Event.objects.create(
            title="Containing Event",
            starts_at=timezone.now() + timedelta(days=1, hours=9),
            ends_at=timezone.now() + timedelta(days=1, hours=14),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=containing)
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].id, containing.id)

    def test_conflict_when_event_is_contained(self):
        """Є конфлікт, якщо подія повністю міститься в іншій"""
        # Подія 10:30-11:30 (міститься в base_event 10:00-12:00)
        contained = Event.objects.create(
            title="Contained Event",
            starts_at=timezone.now() + timedelta(days=1, hours=10, minutes=30),
            ends_at=timezone.now() + timedelta(days=1, hours=11, minutes=30),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=contained)
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].id, contained.id)

    def test_no_conflict_when_events_touch_at_boundary(self):
        """Немає конфлікту, якщо події стикаються на межі (одна закінчується, інша починається)"""
        # Подія 12:00-14:00 (починається коли base_event закінчується)
        touching = Event.objects.create(
            title="Touching Event",
            starts_at=timezone.now() + timedelta(days=1, hours=12),
            ends_at=timezone.now() + timedelta(days=1, hours=14),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=touching)
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(conflicts, [])

    def test_ignores_cancelled_rsvp(self):
        """Ігнорує RSVP зі статусом не 'going'"""
        overlapping = Event.objects.create(
            title="Overlapping Event",
            starts_at=timezone.now() + timedelta(days=1, hours=11),
            ends_at=timezone.now() + timedelta(days=1, hours=13),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=overlapping, status="cancelled")
        
        conflicts = RSVPService.get_conflicting_events(self.user, self.base_event)
        self.assertEqual(conflicts, [])


class CheckTimeConflictTests(RSVPServiceBaseTests):
    """Тести для check_time_conflict"""

    def test_no_conflict_returns_false_none(self):
        """Без конфлікту повертає (False, None)"""
        has_conflict, conflicting = RSVPService.check_time_conflict(self.user, self.base_event)
        
        self.assertFalse(has_conflict)
        self.assertIsNone(conflicting)

    def test_conflict_returns_true_and_event(self):
        """З конфліктом повертає (True, Event)"""
        overlapping = Event.objects.create(
            title="Overlapping Event",
            starts_at=timezone.now() + timedelta(days=1, hours=11),
            ends_at=timezone.now() + timedelta(days=1, hours=13),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=overlapping)
        
        has_conflict, conflicting = RSVPService.check_time_conflict(self.user, self.base_event)
        
        self.assertTrue(has_conflict)
        self.assertEqual(conflicting.id, overlapping.id)


class CanCreateRsvpTests(RSVPServiceBaseTests):
    """Тести для can_create_rsvp"""

    def test_can_create_when_no_issues(self):
        """Можна створити RSVP, якщо немає проблем"""
        can_create, error = RSVPService.can_create_rsvp(self.user, self.base_event)
        
        self.assertTrue(can_create)
        self.assertIsNone(error)

    def test_cannot_create_when_already_registered(self):
        """Не можна створити RSVP, якщо вже зареєстрований"""
        RSVP.objects.create(user=self.user, event=self.base_event)
        
        can_create, error = RSVPService.can_create_rsvp(self.user, self.base_event)
        
        self.assertFalse(can_create)
        self.assertIn("вже зареєстровані", error)

    def test_cannot_create_when_capacity_full(self):
        """Не можна створити RSVP, якщо місця закінчились"""
        self.base_event.capacity = 1
        self.base_event.save()
        
        # Інший користувач займає єдине місце
        RSVP.objects.create(user=self.other_user, event=self.base_event)
        
        can_create, error = RSVPService.can_create_rsvp(self.user, self.base_event)
        
        self.assertFalse(can_create)
        self.assertIn("місця зайняті", error)

    def test_cannot_create_when_time_conflict(self):
        """Не можна створити RSVP, якщо є конфлікт часу"""
        overlapping = Event.objects.create(
            title="Overlapping Event",
            starts_at=timezone.now() + timedelta(days=1, hours=11),
            ends_at=timezone.now() + timedelta(days=1, hours=13),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=overlapping)
        
        can_create, error = RSVPService.can_create_rsvp(self.user, self.base_event)
        
        self.assertFalse(can_create)
        self.assertIn("Конфлікт часу", error)
        self.assertIn("Overlapping Event", error)

    def test_can_create_when_no_time_conflict(self):
        """Можна створити RSVP, якщо немає конфлікту часу"""
        non_overlapping = Event.objects.create(
            title="Non-overlapping Event",
            starts_at=timezone.now() + timedelta(days=1, hours=14),
            ends_at=timezone.now() + timedelta(days=1, hours=16),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        RSVP.objects.create(user=self.user, event=non_overlapping)
        
        can_create, error = RSVPService.can_create_rsvp(self.user, self.base_event)
        
        self.assertTrue(can_create)
        self.assertIsNone(error)
