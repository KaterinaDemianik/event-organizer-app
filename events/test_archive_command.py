"""
Тести для events/management/commands/archive_past_events.py
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
from datetime import timedelta

from events.models import Event


class ArchivePastEventsCommandTestCase(TestCase):
    """Тести для management команди archive_past_events"""

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Минула подія
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        # Майбутня подія
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_archive_past_events_with_events(self):
        """Тест архівування минулих подій"""
        out = StringIO()
        call_command('archive_past_events', stdout=out)
        
        output = out.getvalue()
        # Перевіряємо що команда виконалась
        self.assertTrue(len(output) > 0)

    def test_archive_past_events_no_events(self):
        """Тест коли немає подій для архівування"""
        # Видаляємо минулу подію
        self.past_event.delete()
        
        out = StringIO()
        call_command('archive_past_events', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Немає подій', output)
