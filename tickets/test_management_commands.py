"""
Тести для management commands - покриття fix_rsvp_duplicates команди

ПРИМІТКА: Команда fix_rsvp_duplicates призначена для legacy-даних,
коли UNIQUE constraint ще не був встановлений. Зараз БД має 
UNIQUE(user, event), тому дублікати неможливі в штатному потоці.
Тести перевіряють тільки валідні сценарії без дублікатів.
"""
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from io import StringIO

from tickets.models import RSVP
from events.models import Event


class FixRSVPDuplicatesCommandTestCase(TestCase):
    """Тести для fix_rsvp_duplicates management команди"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123"
        )
        
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123"
        )
        
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event1 = Event.objects.create(
            title="Event 1",
            description="Description 1",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        self.event2 = Event.objects.create(
            title="Event 2",
            description="Description 2",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_fix_rsvp_duplicates_no_duplicates(self):
        """Тест команди коли немає дублікатів"""
        # Створюємо унікальні RSVP
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        RSVP.objects.create(user=self.user1, event=self.event2, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Всього видалено 0 записів RSVP", output)
        
        # Перевіряємо що всі RSVP залишились
        self.assertEqual(RSVP.objects.count(), 3)

    def test_fix_rsvp_duplicates_command_help(self):
        """Тест help тексту команди"""
        from tickets.management.commands.fix_rsvp_duplicates import Command
        
        command = Command()
        self.assertEqual(
            command.help, 
            "Видаляє дублікати RSVP, залишаючи тільки найновіші записи"
        )

    def test_fix_rsvp_duplicates_different_events(self):
        """Тест що команда не чіпає RSVP для різних подій"""
        # Один користувач, різні події - не дублікати
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user1, event=self.event2, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Всього видалено 0 записів RSVP", output)
        
        # Перевіряємо що user1 має RSVP для обох подій
        user1_rsvps = RSVP.objects.filter(user=self.user1)
        self.assertEqual(user1_rsvps.count(), 2)

    def test_fix_rsvp_duplicates_empty_database(self):
        """Тест команди на порожній базі"""
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Всього видалено 0 записів RSVP", output)
        self.assertEqual(RSVP.objects.count(), 0)
