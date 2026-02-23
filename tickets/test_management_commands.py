"""
Тести для management commands - покриття fix_rsvp_duplicates команди
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

    def test_fix_rsvp_duplicates_with_duplicates(self):
        """Тест команди з дублікатами RSVP"""
        # Створюємо дублікати для user1 + event1
        rsvp1 = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        rsvp2 = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        rsvp3 = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        
        # Робимо rsvp2 найновішим (змінюємо created_at)
        rsvp2.created_at = timezone.now() + timedelta(seconds=1)
        rsvp2.save()
        
        initial_count = RSVP.objects.count()
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        
        # Перевіряємо що видалено 2 дублікати
        self.assertIn("Видалено 2 старих RSVP", output)
        self.assertIn("Всього видалено 2 записів RSVP", output)
        
        # Перевіряємо що залишився тільки найновіший
        remaining_rsvps = RSVP.objects.filter(user=self.user1, event=self.event1)
        self.assertEqual(remaining_rsvps.count(), 1)
        self.assertEqual(remaining_rsvps.first().id, rsvp2.id)

    def test_fix_rsvp_duplicates_multiple_users(self):
        """Тест команди з дублікатами для різних користувачів"""
        # Дублікати для user1 + event1
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        
        # Дублікати для user2 + event1
        RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        
        # Унікальний RSVP
        RSVP.objects.create(user=self.user1, event=self.event2, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        
        # Перевіряємо що видалено дублікати для обох користувачів
        self.assertIn("Всього видалено 2 записів RSVP", output)
        
        # Перевіряємо що залишилось 3 унікальних RSVP
        self.assertEqual(RSVP.objects.count(), 3)

    def test_fix_rsvp_duplicates_invalid_status(self):
        """Тест команди з невалідними статусами"""
        # Створюємо RSVP з валідним статусом
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        
        # Створюємо RSVP з невалідними статусами
        RSVP.objects.create(user=self.user2, event=self.event1, status="maybe")
        RSVP.objects.create(user=self.user1, event=self.event2, status="not_going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        
        # Перевіряємо що видалено RSVP з невалідним статусом
        self.assertIn("Видалено 2 RSVP з невалідним статусом", output)
        self.assertIn("Всього видалено 2 записів RSVP", output)
        
        # Перевіряємо що залишився тільки валідний RSVP
        self.assertEqual(RSVP.objects.count(), 1)
        remaining_rsvp = RSVP.objects.first()
        self.assertEqual(remaining_rsvp.status, "going")

    def test_fix_rsvp_duplicates_mixed_scenario(self):
        """Тест команди зі змішаним сценарієм (дублікати + невалідні статуси)"""
        # Дублікати з валідним статусом
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        
        # RSVP з невалідним статусом
        RSVP.objects.create(user=self.user2, event=self.event1, status="maybe")
        
        # Унікальний валідний RSVP
        RSVP.objects.create(user=self.user2, event=self.event2, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        
        # Перевіряємо що видалено і дублікат і невалідний статус
        self.assertIn("Видалено 1 старих RSVP", output)
        self.assertIn("Видалено 1 RSVP з невалідним статусом", output)
        self.assertIn("Всього видалено 2 записів RSVP", output)
        
        # Перевіряємо що залишилось 2 валідних унікальних RSVP
        self.assertEqual(RSVP.objects.count(), 2)
        for rsvp in RSVP.objects.all():
            self.assertEqual(rsvp.status, "going")

    def test_fix_rsvp_duplicates_no_invalid_status(self):
        """Тест команди коли немає невалідних статусів"""
        # Створюємо тільки валідні RSVP
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        
        # Перевіряємо що не було повідомлення про невалідні статуси
        self.assertNotIn("невалідним статусом", output)
        self.assertIn("Всього видалено 0 записів RSVP", output)

    def test_fix_rsvp_duplicates_command_help(self):
        """Тест help тексту команди"""
        from tickets.management.commands.fix_rsvp_duplicates import Command
        
        command = Command()
        self.assertEqual(
            command.help, 
            "Видаляє дублікати RSVP, залишаючи тільки найновіші записи"
        )

    def test_fix_rsvp_duplicates_preserves_latest(self):
        """Тест що команда зберігає саме найновіший запис"""
        # Створюємо 3 дублікати з різним часом створення
        now = timezone.now()
        
        rsvp_old = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        rsvp_old.created_at = now - timedelta(hours=2)
        rsvp_old.save()
        
        rsvp_middle = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        rsvp_middle.created_at = now - timedelta(hours=1)
        rsvp_middle.save()
        
        rsvp_latest = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        rsvp_latest.created_at = now
        rsvp_latest.save()
        
        call_command('fix_rsvp_duplicates', stdout=StringIO())
        
        # Перевіряємо що залишився саме найновіший
        remaining_rsvps = RSVP.objects.filter(user=self.user1, event=self.event1)
        self.assertEqual(remaining_rsvps.count(), 1)
        self.assertEqual(remaining_rsvps.first().id, rsvp_latest.id)

    def test_fix_rsvp_duplicates_different_events(self):
        """Тест що команда не чіпає RSVP для різних подій"""
        # Один користувач, різні події - не дублікати
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user1, event=self.event2, status="going")
        
        # Дублікати для однієї події
        RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        
        call_command('fix_rsvp_duplicates', stdout=StringIO())
        
        # Перевіряємо що залишилось 3 RSVP (2 для user1 + 1 для user2)
        self.assertEqual(RSVP.objects.count(), 3)
        
        # Перевіряємо що user1 має RSVP для обох подій
        user1_rsvps = RSVP.objects.filter(user=self.user1)
        self.assertEqual(user1_rsvps.count(), 2)
        
        # Перевіряємо що user2 має тільки 1 RSVP
        user2_rsvps = RSVP.objects.filter(user=self.user2)
        self.assertEqual(user2_rsvps.count(), 1)
