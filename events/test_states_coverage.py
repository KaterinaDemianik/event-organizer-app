"""
Тести для events/states.py - повне покриття State Pattern
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import MagicMock

from events.models import Event
from events.states import (
    EventState,
    DraftState,
    PublishedState,
    CancelledState,
    ArchivedState,
    STATE_CLASSES,
    EventStateManager,
)


class DraftStateTestCase(TestCase):
    """Тести для DraftState"""

    def setUp(self):
        self.state = DraftState()

    def test_draft_state_name(self):
        """Тест назви стану"""
        self.assertEqual(self.state.name, "draft")

    def test_draft_state_can_edit(self):
        """Тест що чернетку можна редагувати"""
        self.assertTrue(self.state.can_edit())

    def test_draft_state_can_cancel(self):
        """Тест що чернетку можна скасувати"""
        self.assertTrue(self.state.can_cancel())

    def test_draft_state_can_archive(self):
        """Тест що чернетку не можна архівувати"""
        self.assertFalse(self.state.can_archive())

    def test_draft_state_can_publish(self):
        """Тест що чернетку можна опублікувати"""
        self.assertTrue(self.state.can_publish())

    def test_draft_state_allowed_transitions(self):
        """Тест дозволених переходів з чернетки"""
        transitions = self.state.get_allowed_transitions()
        self.assertEqual(transitions, {"published", "cancelled"})

    def test_draft_state_available_actions(self):
        """Тест доступних дій для чернетки"""
        actions = self.state.get_available_actions()
        self.assertIn("edit", actions)
        self.assertIn("publish", actions)
        self.assertIn("cancel", actions)
        self.assertNotIn("archive", actions)


class PublishedStateTestCase(TestCase):
    """Тести для PublishedState"""

    def setUp(self):
        self.state = PublishedState()

    def test_published_state_name(self):
        """Тест назви стану"""
        self.assertEqual(self.state.name, "published")

    def test_published_state_can_edit(self):
        """Тест що опубліковану подію можна редагувати"""
        self.assertTrue(self.state.can_edit())

    def test_published_state_can_cancel(self):
        """Тест що опубліковану подію можна скасувати"""
        self.assertTrue(self.state.can_cancel())

    def test_published_state_can_archive(self):
        """Тест що опубліковану подію можна архівувати"""
        self.assertTrue(self.state.can_archive())

    def test_published_state_can_publish(self):
        """Тест що опубліковану подію не можна опублікувати повторно"""
        self.assertFalse(self.state.can_publish())

    def test_published_state_allowed_transitions(self):
        """Тест дозволених переходів з опублікованої"""
        transitions = self.state.get_allowed_transitions()
        self.assertEqual(transitions, {"cancelled", "archived"})

    def test_published_state_available_actions(self):
        """Тест доступних дій для опублікованої події"""
        actions = self.state.get_available_actions()
        self.assertIn("edit", actions)
        self.assertIn("cancel", actions)
        self.assertIn("archive", actions)
        self.assertNotIn("publish", actions)


class CancelledStateTestCase(TestCase):
    """Тести для CancelledState"""

    def setUp(self):
        self.state = CancelledState()

    def test_cancelled_state_name(self):
        """Тест назви стану"""
        self.assertEqual(self.state.name, "cancelled")

    def test_cancelled_state_can_edit(self):
        """Тест що скасовану подію не можна редагувати"""
        self.assertFalse(self.state.can_edit())

    def test_cancelled_state_can_cancel(self):
        """Тест що скасовану подію не можна скасувати повторно"""
        self.assertFalse(self.state.can_cancel())

    def test_cancelled_state_can_archive(self):
        """Тест що скасовану подію не можна архівувати"""
        self.assertFalse(self.state.can_archive())

    def test_cancelled_state_can_publish(self):
        """Тест що скасовану подію не можна опублікувати"""
        self.assertFalse(self.state.can_publish())

    def test_cancelled_state_allowed_transitions(self):
        """Тест що зі скасованої події немає переходів"""
        transitions = self.state.get_allowed_transitions()
        self.assertEqual(transitions, set())

    def test_cancelled_state_available_actions(self):
        """Тест що для скасованої події немає доступних дій"""
        actions = self.state.get_available_actions()
        self.assertEqual(actions, [])


class ArchivedStateTestCase(TestCase):
    """Тести для ArchivedState"""

    def setUp(self):
        self.state = ArchivedState()

    def test_archived_state_name(self):
        """Тест назви стану"""
        self.assertEqual(self.state.name, "archived")

    def test_archived_state_can_edit(self):
        """Тест що архівовану подію не можна редагувати"""
        self.assertFalse(self.state.can_edit())

    def test_archived_state_can_cancel(self):
        """Тест що архівовану подію не можна скасувати"""
        self.assertFalse(self.state.can_cancel())

    def test_archived_state_can_archive(self):
        """Тест що архівовану подію не можна архівувати повторно"""
        self.assertFalse(self.state.can_archive())

    def test_archived_state_can_publish(self):
        """Тест що архівовану подію не можна опублікувати"""
        self.assertFalse(self.state.can_publish())

    def test_archived_state_allowed_transitions(self):
        """Тест що з архівованої події немає переходів"""
        transitions = self.state.get_allowed_transitions()
        self.assertEqual(transitions, set())

    def test_archived_state_available_actions(self):
        """Тест що для архівованої події немає доступних дій"""
        actions = self.state.get_available_actions()
        self.assertEqual(actions, [])


class StateClassesTestCase(TestCase):
    """Тести для STATE_CLASSES словника"""

    def test_state_classes_contains_all_states(self):
        """Тест що словник містить всі стани"""
        self.assertIn("draft", STATE_CLASSES)
        self.assertIn("published", STATE_CLASSES)
        self.assertIn("cancelled", STATE_CLASSES)
        self.assertIn("archived", STATE_CLASSES)

    def test_state_classes_correct_types(self):
        """Тест що стани мають правильні типи"""
        self.assertIsInstance(STATE_CLASSES["draft"], DraftState)
        self.assertIsInstance(STATE_CLASSES["published"], PublishedState)
        self.assertIsInstance(STATE_CLASSES["cancelled"], CancelledState)
        self.assertIsInstance(STATE_CLASSES["archived"], ArchivedState)


class EventStateManagerTestCase(TestCase):
    """Тести для EventStateManager"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Майбутня подія
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Завершена подія
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=1),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Чернетка
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Description",
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=2),
            organizer=self.user,
            status=Event.DRAFT
        )
        
        # Скасована подія
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=4),
            ends_at=now + timedelta(days=4, hours=2),
            organizer=self.user,
            status=Event.CANCELLED
        )
        
        # Архівована подія
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.user,
            status=Event.ARCHIVED
        )

    def test_get_state_draft(self):
        """Тест отримання стану для чернетки"""
        state = EventStateManager.get_state("draft")
        self.assertIsInstance(state, DraftState)

    def test_get_state_published(self):
        """Тест отримання стану для опублікованої"""
        state = EventStateManager.get_state("published")
        self.assertIsInstance(state, PublishedState)

    def test_get_state_cancelled(self):
        """Тест отримання стану для скасованої"""
        state = EventStateManager.get_state("cancelled")
        self.assertIsInstance(state, CancelledState)

    def test_get_state_archived(self):
        """Тест отримання стану для архівованої"""
        state = EventStateManager.get_state("archived")
        self.assertIsInstance(state, ArchivedState)

    def test_get_state_unknown_returns_draft(self):
        """Тест що невідомий статус повертає draft"""
        state = EventStateManager.get_state("unknown_status")
        self.assertIsInstance(state, DraftState)

    def test_can_transition_draft_to_published(self):
        """Тест переходу draft -> published"""
        self.assertTrue(EventStateManager.can_transition("draft", "published"))

    def test_can_transition_draft_to_cancelled(self):
        """Тест переходу draft -> cancelled"""
        self.assertTrue(EventStateManager.can_transition("draft", "cancelled"))

    def test_can_transition_draft_to_archived_not_allowed(self):
        """Тест що перехід draft -> archived не дозволений"""
        self.assertFalse(EventStateManager.can_transition("draft", "archived"))

    def test_can_transition_published_to_cancelled(self):
        """Тест переходу published -> cancelled"""
        self.assertTrue(EventStateManager.can_transition("published", "cancelled"))

    def test_can_transition_published_to_archived(self):
        """Тест переходу published -> archived"""
        self.assertTrue(EventStateManager.can_transition("published", "archived"))

    def test_can_transition_cancelled_no_transitions(self):
        """Тест що зі скасованої немає переходів"""
        self.assertFalse(EventStateManager.can_transition("cancelled", "published"))
        self.assertFalse(EventStateManager.can_transition("cancelled", "archived"))
        self.assertFalse(EventStateManager.can_transition("cancelled", "draft"))

    def test_can_transition_archived_no_transitions(self):
        """Тест що з архівованої немає переходів"""
        self.assertFalse(EventStateManager.can_transition("archived", "published"))
        self.assertFalse(EventStateManager.can_transition("archived", "cancelled"))
        self.assertFalse(EventStateManager.can_transition("archived", "draft"))

    def test_validate_transition_same_status(self):
        """Тест валідації переходу в той же статус"""
        is_valid, error = EventStateManager.validate_transition(self.future_event, "published")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_transition_draft_to_published(self):
        """Тест валідації переходу draft -> published"""
        is_valid, error = EventStateManager.validate_transition(self.draft_event, "published")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_transition_invalid(self):
        """Тест валідації невалідного переходу"""
        is_valid, error = EventStateManager.validate_transition(self.draft_event, "archived")
        self.assertFalse(is_valid)
        self.assertIn("неможливий", error)

    def test_validate_transition_archive_future_event(self):
        """Тест що не можна архівувати майбутню подію"""
        is_valid, error = EventStateManager.validate_transition(self.future_event, "archived")
        self.assertFalse(is_valid)
        self.assertIn("завершені", error)

    def test_validate_transition_archive_past_event(self):
        """Тест що можна архівувати завершену подію"""
        is_valid, error = EventStateManager.validate_transition(self.past_event, "archived")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_transition_archive_non_published(self):
        """Тест що не можна архівувати неопубліковану подію"""
        # Створюємо завершену чернетку
        past_draft = Event.objects.create(
            title="Past Draft",
            description="Description",
            starts_at=timezone.now() - timedelta(days=3),
            ends_at=timezone.now() - timedelta(days=2),
            organizer=self.user,
            status=Event.DRAFT
        )
        is_valid, error = EventStateManager.validate_transition(past_draft, "archived")
        self.assertFalse(is_valid)
        self.assertIn("неможливий", error)

    def test_get_available_actions_draft(self):
        """Тест доступних дій для чернетки"""
        actions = EventStateManager.get_available_actions(self.draft_event)
        self.assertIn("edit", actions)
        self.assertIn("publish", actions)
        self.assertIn("cancel", actions)
        self.assertNotIn("archive", actions)

    def test_get_available_actions_published_future(self):
        """Тест доступних дій для майбутньої опублікованої події"""
        actions = EventStateManager.get_available_actions(self.future_event)
        self.assertIn("edit", actions)
        self.assertIn("cancel", actions)
        # archive не доступний для майбутньої події
        self.assertNotIn("archive", actions)

    def test_get_available_actions_published_past(self):
        """Тест доступних дій для завершеної опублікованої події"""
        actions = EventStateManager.get_available_actions(self.past_event)
        self.assertIn("edit", actions)
        self.assertIn("cancel", actions)
        self.assertIn("archive", actions)

    def test_get_available_actions_cancelled(self):
        """Тест доступних дій для скасованої події"""
        actions = EventStateManager.get_available_actions(self.cancelled_event)
        self.assertEqual(actions, [])

    def test_get_available_actions_archived(self):
        """Тест доступних дій для архівованої події"""
        actions = EventStateManager.get_available_actions(self.archived_event)
        self.assertEqual(actions, [])

    def test_can_edit_draft(self):
        """Тест чи можна редагувати чернетку"""
        self.assertTrue(EventStateManager.can_edit(self.draft_event))

    def test_can_edit_published(self):
        """Тест чи можна редагувати опубліковану"""
        self.assertTrue(EventStateManager.can_edit(self.future_event))

    def test_can_edit_cancelled(self):
        """Тест чи можна редагувати скасовану"""
        self.assertFalse(EventStateManager.can_edit(self.cancelled_event))

    def test_can_edit_archived(self):
        """Тест чи можна редагувати архівовану"""
        self.assertFalse(EventStateManager.can_edit(self.archived_event))

    def test_can_cancel_draft(self):
        """Тест чи можна скасувати чернетку"""
        self.assertTrue(EventStateManager.can_cancel(self.draft_event))

    def test_can_cancel_published(self):
        """Тест чи можна скасувати опубліковану"""
        self.assertTrue(EventStateManager.can_cancel(self.future_event))

    def test_can_cancel_cancelled(self):
        """Тест чи можна скасувати скасовану"""
        self.assertFalse(EventStateManager.can_cancel(self.cancelled_event))

    def test_can_cancel_archived(self):
        """Тест чи можна скасувати архівовану"""
        self.assertFalse(EventStateManager.can_cancel(self.archived_event))

    def test_can_archive_draft(self):
        """Тест чи можна архівувати чернетку"""
        self.assertFalse(EventStateManager.can_archive(self.draft_event))

    def test_can_archive_published_future(self):
        """Тест чи можна архівувати майбутню опубліковану"""
        self.assertFalse(EventStateManager.can_archive(self.future_event))

    def test_can_archive_published_past(self):
        """Тест чи можна архівувати завершену опубліковану"""
        self.assertTrue(EventStateManager.can_archive(self.past_event))

    def test_can_archive_cancelled(self):
        """Тест чи можна архівувати скасовану"""
        self.assertFalse(EventStateManager.can_archive(self.cancelled_event))

    def test_can_archive_archived(self):
        """Тест чи можна архівувати архівовану"""
        self.assertFalse(EventStateManager.can_archive(self.archived_event))
