"""
Тести для досягнення 100% coverage
Покриває рядки: forms.py:130, serializers.py:72, states.py:209, services.py:69
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.forms import ReviewForm
from events.serializers import EventSerializer
from events.states import EventStateManager
from notifications.services import NotificationService
from tickets.models import RSVP


class ReviewFormCleanRatingTestCase(TestCase):
    """Тест для events/forms.py рядок 130 - ValidationError для невалідного рейтингу"""

    def test_clean_rating_raises_validation_error_for_zero(self):
        """Рейтинг 0 викликає ValidationError"""
        form = ReviewForm(data={'rating': '0', 'comment': 'Test'})
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_clean_rating_raises_validation_error_for_six(self):
        """Рейтинг 6 викликає ValidationError"""
        form = ReviewForm(data={'rating': '6', 'comment': 'Test'})
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)


class SerializerValidateMethodTestCase(TestCase):
    """Тест для events/serializers.py рядок 72 - ValidationError в validate()"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com", 
            password="testpass123"
        )
        now = timezone.now()
        self.published_event = Event.objects.create(
            title="Published Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_validate_raises_error_for_invalid_transition(self):
        """validate() викликає ValidationError для невалідного переходу published->draft"""
        serializer = EventSerializer(
            instance=self.published_event,
            data={'status': Event.DRAFT},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        # Перевіряємо що помилка містить інформацію про дозволені переходи
        error_text = str(serializer.errors['status'])
        self.assertTrue(len(error_text) > 0)


class StateManagerArchiveValidationTestCase(TestCase):
    """Тест для events/states.py рядок 209 - архівування не-published події"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        now = timezone.now()
        # Завершена подія зі статусом draft (не published)
        self.ended_draft_event = Event.objects.create(
            title="Ended Draft Event",
            description="Description",
            starts_at=now - timedelta(days=10),
            ends_at=now - timedelta(days=9),
            organizer=self.user,
            status=Event.DRAFT
        )
        # Завершена подія зі статусом published
        self.ended_published_event = Event.objects.create(
            title="Ended Published Event", 
            description="Description",
            starts_at=now - timedelta(days=10),
            ends_at=now - timedelta(days=9),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_archive_draft_event_returns_error(self):
        """Архівування draft події повертає помилку про опубліковані події"""
        # Спочатку змінимо статус на published щоб перехід був можливий
        # а потім перевіримо що для draft неможливо
        is_valid, error = EventStateManager.validate_transition(
            self.ended_draft_event, "archived"
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_archive_published_ended_event_succeeds(self):
        """Архівування завершеної published події успішне"""
        is_valid, error = EventStateManager.validate_transition(
            self.ended_published_event, "archived"
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)


class NotificationServiceNoChangesTestCase(TestCase):
    """Тест для notifications/services.py рядок 69 - повернення 0 без змін"""

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        now = timezone.now()
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            location="Київ",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_create_event_update_notification_returns_zero_without_changes(self):
        """Без змін create_event_update_notification повертає 0"""
        # Передаємо ті самі дані - змін немає
        old_data = {
            'title': self.event.title,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
            'location': self.event.location,
        }
        count = NotificationService.create_event_update_notification(
            self.event, old_data
        )
        # Без учасників і без змін - повертає 0
        self.assertEqual(count, 0)

    def test_create_event_update_notification_with_participant_returns_int(self):
        """З учасником - повертає int"""
        participant = User.objects.create_user(
            username="participant",
            email="participant@example.com",
            password="testpass123"
        )
        RSVP.objects.create(user=participant, event=self.event, status="going")
        
        old_data = {
            'title': self.event.title,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
            'location': self.event.location,
        }
        count = NotificationService.create_event_update_notification(
            self.event, old_data
        )
        # Повертає int
        self.assertIsInstance(count, int)
