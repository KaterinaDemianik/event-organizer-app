"""
Фінальні тести для досягнення 100% coverage
Покриває останні непокриті рядки
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.forms import ReviewForm
from events.states import EventStateManager
from events.serializers import EventSerializer
from notifications.services import NotificationService
from tickets.models import RSVP


class ReviewFormRatingValidationTestCase(TestCase):
    """Тести для events/forms.py - рядок 130"""

    def test_rating_invalid_value_raises_error(self):
        """Тест що невалідний рейтинг викликає помилку - рядок 130"""
        # Тестуємо рейтинг 0 (менше 1)
        form = ReviewForm(data={
            'rating': '0',
            'comment': 'Test comment'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_rating_too_high_raises_error(self):
        """Тест що рейтинг > 5 викликає помилку"""
        form = ReviewForm(data={
            'rating': '6',
            'comment': 'Test comment'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)


class EventStateManagerArchiveValidationTestCase(TestCase):
    """Тести для events/states.py - рядок 209"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Завершена published подія - можна архівувати
        self.ended_published_event = Event.objects.create(
            title="Ended Published Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=5, hours=-2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Завершена draft подія - не можна архівувати (рядок 209)
        self.ended_draft_event = Event.objects.create(
            title="Ended Draft Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=5, hours=-2),
            organizer=self.user,
            status=Event.DRAFT
        )

    def test_archive_ended_published_event_allowed(self):
        """Тест: архівування завершеної published події дозволено"""
        is_valid, error = EventStateManager.validate_transition(
            self.ended_published_event, "archived"
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_archive_ended_draft_event_forbidden(self):
        """Тест: архівування завершеної draft події заборонено - рядок 209"""
        # Draft подія не може перейти в archived напряму
        is_valid, error = EventStateManager.validate_transition(
            self.ended_draft_event, "archived"
        )
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class EventSerializerValidateMethodTestCase(TestCase):
    """Тести для events/serializers.py - рядок 72"""

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

    def test_validate_blocks_transition_to_draft(self):
        """Тест що validate() блокує перехід published -> draft - рядок 72"""
        serializer = EventSerializer(
            instance=self.published_event,
            data={'status': Event.DRAFT},
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)


class NotificationServicesNoChangesTestCase(TestCase):
    """Тести для notifications/services.py - рядок 69"""

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
            location="Київ",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        # Додаємо учасника
        RSVP.objects.create(user=self.user, event=self.event, status="going")

    def test_create_event_update_notification_returns_count(self):
        """Тест що функція повертає кількість сповіщень"""
        old_data = {
            'title': self.event.title,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
            'location': self.event.location,
        }
        
        count = NotificationService.create_event_update_notification(
            self.event, old_data
        )
        
        # Функція повертає число
        self.assertIsInstance(count, int)


class ScheduleServicesTypeCheckingTestCase(TestCase):
    """Тести для events/schedule_services.py - рядок 23 (TYPE_CHECKING)"""

    def test_schedule_entry_import(self):
        """Тест імпорту ScheduleEntry"""
        from events.schedule_services import ScheduleEntry
        
        now = timezone.now()
        entry = ScheduleEntry(
            event_id=1,
            title="Test",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="published",
            location="Київ",
            description="Desc",
            is_organizer=True,
            has_rsvp=False
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.title, "Test")
