"""
Тести для tickets/management/commands/fix_rsvp_duplicates.py
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
from datetime import timedelta

from events.models import Event
from tickets.models import RSVP


class FixRSVPDuplicatesCommandTestCase(TestCase):
    """Тести для management команди fix_rsvp_duplicates"""

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
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        self.event2 = Event.objects.create(
            title="Test Event 2",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_command_no_duplicates(self):
        """Тест команди коли немає дублікатів"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Всього видалено', output)

    def test_command_with_invalid_status(self):
        """Тест команди з невалідним статусом RSVP"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        RSVP.objects.create(user=self.user2, event=self.event, status="maybe")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('невалідним статусом', output)
        
        # Перевіряємо що RSVP з невалідним статусом видалено
        self.assertEqual(RSVP.objects.filter(status="maybe").count(), 0)

    def test_command_empty_database(self):
        """Тест команди з порожньою базою"""
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Всього видалено 0', output)
