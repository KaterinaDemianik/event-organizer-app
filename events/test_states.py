"""
Тести для State Pattern (управління станами подій)
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Event
from .states import (
    EventStateManager,
    DraftState,
    PublishedState,
    CancelledState,
    ArchivedState,
)

User = get_user_model()


class StatePatternTests(TestCase):
    """Тести для State Pattern"""

    def setUp(self):
        self.user = User.objects.create_user(username="organizer", password="pass")
        
        self.draft_event = Event.objects.create(
            title="Draft Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.DRAFT,
            organizer=self.user,
        )
        
        self.published_event = Event.objects.create(
            title="Published Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.user,
        )
        
        self.past_published_event = Event.objects.create(
            title="Past Published Event",
            starts_at=timezone.now() - timezone.timedelta(days=2),
            ends_at=timezone.now() - timezone.timedelta(days=1),
            status=Event.PUBLISHED,
            organizer=self.user,
        )
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.CANCELLED,
            organizer=self.user,
        )
        
        self.archived_event = Event.objects.create(
            title="Archived Event",
            starts_at=timezone.now() - timezone.timedelta(days=3),
            ends_at=timezone.now() - timezone.timedelta(days=2),
            status=Event.ARCHIVED,
            organizer=self.user,
        )


class CanTransitionTests(StatePatternTests):
    """Тести для can_transition"""

    def test_draft_can_transition_to_published(self):
        """Чернетка може бути опублікована"""
        self.assertTrue(EventStateManager.can_transition("draft", "published"))

    def test_draft_cannot_transition_to_archived(self):
        """Чернетка не може бути архівована напряму"""
        self.assertFalse(EventStateManager.can_transition("draft", "archived"))

    def test_draft_can_transition_to_cancelled(self):
        """Чернетка може бути скасована"""
        self.assertTrue(EventStateManager.can_transition("draft", "cancelled"))

    def test_published_can_transition_to_cancelled(self):
        """Опублікована подія може бути скасована"""
        self.assertTrue(EventStateManager.can_transition("published", "cancelled"))

    def test_published_can_transition_to_archived(self):
        """Опублікована подія може бути архівована"""
        self.assertTrue(EventStateManager.can_transition("published", "archived"))

    def test_cancelled_cannot_transition(self):
        """Скасована подія не може змінювати стан"""
        self.assertFalse(EventStateManager.can_transition("cancelled", "published"))
        self.assertFalse(EventStateManager.can_transition("cancelled", "archived"))
        self.assertFalse(EventStateManager.can_transition("cancelled", "draft"))

    def test_archived_cannot_transition(self):
        """Архівована подія не може змінювати стан"""
        self.assertFalse(EventStateManager.can_transition("archived", "published"))
        self.assertFalse(EventStateManager.can_transition("archived", "cancelled"))
        self.assertFalse(EventStateManager.can_transition("archived", "draft"))


class ValidateTransitionTests(StatePatternTests):
    """Тести для validate_transition з бізнес-правилами"""

    def test_archive_requires_past_event(self):
        """Архівувати можна лише завершені події"""
        is_valid, error = EventStateManager.validate_transition(
            self.published_event, "archived"
        )
        self.assertFalse(is_valid)
        self.assertIn("завершені", error)

    def test_archive_past_published_event_valid(self):
        """Завершена опублікована подія може бути архівована"""
        is_valid, error = EventStateManager.validate_transition(
            self.past_published_event, "archived"
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_archive_draft_invalid(self):
        """Чернетка не може бути архівована"""
        is_valid, error = EventStateManager.validate_transition(
            self.draft_event, "archived"
        )
        self.assertFalse(is_valid)

    def test_cancel_published_valid(self):
        """Опублікована подія може бути скасована"""
        is_valid, error = EventStateManager.validate_transition(
            self.published_event, "cancelled"
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_cancel_archived_invalid(self):
        """Архівована подія не може бути скасована"""
        is_valid, error = EventStateManager.validate_transition(
            self.archived_event, "cancelled"
        )
        self.assertFalse(is_valid)

    def test_same_status_transition_valid(self):
        """Перехід до того ж статусу валідний (no-op)"""
        is_valid, error = EventStateManager.validate_transition(
            self.published_event, "published"
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class GetAvailableActionsTests(StatePatternTests):
    """Тести для get_available_actions"""

    def test_draft_actions(self):
        """Чернетка: можна редагувати, публікувати та скасувати"""
        actions = EventStateManager.get_available_actions(self.draft_event)
        self.assertIn("edit", actions)
        self.assertIn("publish", actions)
        self.assertIn("cancel", actions)
        self.assertNotIn("archive", actions)

    def test_published_future_event_actions(self):
        """Опублікована майбутня подія: редагування, скасування, без архівації"""
        actions = EventStateManager.get_available_actions(self.published_event)
        self.assertIn("edit", actions)
        self.assertIn("cancel", actions)
        self.assertNotIn("archive", actions)

    def test_published_past_event_actions(self):
        """Опублікована завершена подія: редагування, скасування, архівація"""
        actions = EventStateManager.get_available_actions(self.past_published_event)
        self.assertIn("edit", actions)
        self.assertIn("cancel", actions)
        self.assertIn("archive", actions)

    def test_cancelled_event_no_actions(self):
        """Скасована подія: жодних дій"""
        actions = EventStateManager.get_available_actions(self.cancelled_event)
        self.assertEqual(actions, [])

    def test_archived_event_no_actions(self):
        """Архівована подія: жодних дій"""
        actions = EventStateManager.get_available_actions(self.archived_event)
        self.assertEqual(actions, [])


class CanEditTests(StatePatternTests):
    """Тести для can_edit"""

    def test_can_edit_draft(self):
        """Чернетку можна редагувати"""
        self.assertTrue(EventStateManager.can_edit(self.draft_event))

    def test_can_edit_published(self):
        """Опубліковану подію можна редагувати"""
        self.assertTrue(EventStateManager.can_edit(self.published_event))

    def test_cannot_edit_cancelled(self):
        """Скасовану подію не можна редагувати"""
        self.assertFalse(EventStateManager.can_edit(self.cancelled_event))

    def test_cannot_edit_archived(self):
        """Архівовану подію не можна редагувати"""
        self.assertFalse(EventStateManager.can_edit(self.archived_event))


class CanCancelTests(StatePatternTests):
    """Тести для can_cancel"""

    def test_can_cancel_draft(self):
        """Чернетку можна скасувати"""
        self.assertTrue(EventStateManager.can_cancel(self.draft_event))

    def test_can_cancel_published(self):
        """Опубліковану подію можна скасувати"""
        self.assertTrue(EventStateManager.can_cancel(self.published_event))

    def test_cannot_cancel_cancelled(self):
        """Вже скасовану подію не можна скасувати"""
        self.assertFalse(EventStateManager.can_cancel(self.cancelled_event))

    def test_cannot_cancel_archived(self):
        """Архівовану подію не можна скасувати"""
        self.assertFalse(EventStateManager.can_cancel(self.archived_event))


class CanArchiveTests(StatePatternTests):
    """Тести для can_archive"""

    def test_cannot_archive_draft(self):
        """Чернетку не можна архівувати"""
        self.assertFalse(EventStateManager.can_archive(self.draft_event))

    def test_cannot_archive_future_published(self):
        """Майбутню опубліковану подію не можна архівувати"""
        self.assertFalse(EventStateManager.can_archive(self.published_event))

    def test_can_archive_past_published(self):
        """Завершену опубліковану подію можна архівувати"""
        self.assertTrue(EventStateManager.can_archive(self.past_published_event))

    def test_cannot_archive_cancelled(self):
        """Скасовану подію не можна архівувати"""
        self.assertFalse(EventStateManager.can_archive(self.cancelled_event))

    def test_cannot_archive_archived(self):
        """Вже архівовану подію не можна архівувати"""
        self.assertFalse(EventStateManager.can_archive(self.archived_event))


class StateClassesTests(TestCase):
    """Тести для окремих класів станів"""

    def test_draft_state_properties(self):
        """Перевірка властивостей DraftState"""
        state = DraftState()
        self.assertEqual(state.name, "draft")
        self.assertTrue(state.can_edit())
        self.assertTrue(state.can_publish())
        self.assertTrue(state.can_cancel())
        self.assertFalse(state.can_archive())
        self.assertEqual(state.get_allowed_transitions(), {"published", "cancelled"})

    def test_published_state_properties(self):
        """Перевірка властивостей PublishedState"""
        state = PublishedState()
        self.assertEqual(state.name, "published")
        self.assertTrue(state.can_edit())
        self.assertFalse(state.can_publish())
        self.assertTrue(state.can_cancel())
        self.assertTrue(state.can_archive())
        self.assertEqual(state.get_allowed_transitions(), {"cancelled", "archived"})

    def test_cancelled_state_properties(self):
        """Перевірка властивостей CancelledState"""
        state = CancelledState()
        self.assertEqual(state.name, "cancelled")
        self.assertFalse(state.can_edit())
        self.assertFalse(state.can_publish())
        self.assertFalse(state.can_cancel())
        self.assertFalse(state.can_archive())
        self.assertEqual(state.get_allowed_transitions(), set())

    def test_archived_state_properties(self):
        """Перевірка властивостей ArchivedState"""
        state = ArchivedState()
        self.assertEqual(state.name, "archived")
        self.assertFalse(state.can_edit())
        self.assertFalse(state.can_publish())
        self.assertFalse(state.can_cancel())
        self.assertFalse(state.can_archive())
        self.assertEqual(state.get_allowed_transitions(), set())
