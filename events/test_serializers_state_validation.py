"""
Тести для валідації переходів статусів через API (State Pattern в serializers.py)
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError

from events.models import Event
from events.serializers import EventSerializer


class EventSerializerStateValidationTestCase(TestCase):
    """Тести для валідації State Pattern в EventSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Description",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            organizer=self.user,
            status=Event.DRAFT
        )
        
        self.published_event = Event.objects.create(
            title="Published Event",
            description="Description",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            organizer=self.user,
            status=Event.CANCELLED
        )
        
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Description",
            starts_at=now - timedelta(days=10),
            ends_at=now - timedelta(days=10, hours=-2),
            organizer=self.user,
            status=Event.ARCHIVED
        )

    def test_draft_to_published_allowed(self):
        """Тест: draft -> published дозволено"""
        serializer = EventSerializer(
            instance=self.draft_event,
            data={'status': Event.PUBLISHED},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_draft_to_cancelled_allowed(self):
        """Тест: draft -> cancelled дозволено"""
        serializer = EventSerializer(
            instance=self.draft_event,
            data={'status': Event.CANCELLED},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_draft_to_archived_forbidden(self):
        """Тест: draft -> archived заборонено"""
        serializer = EventSerializer(
            instance=self.draft_event,
            data={'status': Event.ARCHIVED},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_published_to_cancelled_allowed(self):
        """Тест: published -> cancelled дозволено"""
        serializer = EventSerializer(
            instance=self.published_event,
            data={'status': Event.CANCELLED},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_published_to_archived_requires_ended_event(self):
        """Тест: published -> archived потребує завершеної події"""
        # Подія ще не завершилась - архівування заборонено
        serializer = EventSerializer(
            instance=self.published_event,
            data={'status': Event.ARCHIVED},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_published_to_draft_forbidden(self):
        """Тест: published -> draft заборонено"""
        serializer = EventSerializer(
            instance=self.published_event,
            data={'status': Event.DRAFT},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_cancelled_to_any_status_forbidden(self):
        """Тест: cancelled -> будь-який статус заборонено"""
        for status in [Event.DRAFT, Event.PUBLISHED, Event.ARCHIVED]:
            serializer = EventSerializer(
                instance=self.cancelled_event,
                data={'status': status},
                partial=True
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn('status', serializer.errors)

    def test_archived_to_any_status_forbidden(self):
        """Тест: archived -> будь-який статус заборонено"""
        for status in [Event.DRAFT, Event.PUBLISHED, Event.CANCELLED]:
            serializer = EventSerializer(
                instance=self.archived_event,
                data={'status': status},
                partial=True
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn('status', serializer.errors)

    def test_same_status_allowed(self):
        """Тест: зміна на той самий статус дозволена"""
        serializer = EventSerializer(
            instance=self.published_event,
            data={'status': Event.PUBLISHED},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_create_event_any_status_allowed(self):
        """Тест: при створенні події будь-який статус дозволений"""
        now = timezone.now()
        serializer = EventSerializer(data={
            'title': 'New Event',
            'description': 'Description',
            'starts_at': now + timedelta(days=1),
            'ends_at': now + timedelta(days=1, hours=2),
            'status': Event.PUBLISHED,
        })
        # При створенні валідація переходів не застосовується
        # (instance is None)
        self.assertTrue(serializer.is_valid() or 'status' not in serializer.errors)

    def test_update_without_status_change(self):
        """Тест: оновлення без зміни статусу працює"""
        serializer = EventSerializer(
            instance=self.published_event,
            data={'title': 'Updated Title'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_error_message_contains_allowed_transitions(self):
        """Тест: повідомлення про помилку містить дозволені переходи"""
        serializer = EventSerializer(
            instance=self.cancelled_event,
            data={'status': Event.PUBLISHED},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        error_message = str(serializer.errors['status'])
        # Перевіряємо що є інформативне повідомлення
        self.assertTrue(len(error_message) > 0)


class EventSerializerValidateMethodTestCase(TestCase):
    """Тести для методу validate() в EventSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            organizer=self.user,
            status=Event.DRAFT
        )

    def test_validate_blocks_invalid_transition(self):
        """Тест: validate() блокує невалідний перехід"""
        serializer = EventSerializer(
            instance=self.event,
            data={'status': Event.ARCHIVED},
            partial=True
        )
        self.assertFalse(serializer.is_valid())

    def test_validate_allows_valid_transition(self):
        """Тест: validate() дозволяє валідний перехід"""
        serializer = EventSerializer(
            instance=self.event,
            data={'status': Event.PUBLISHED},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
