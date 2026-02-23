"""
Тести для tickets/models.py - покриття RSVP моделі
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from datetime import timedelta

from tickets.models import RSVP
from events.models import Event


class RSVPModelTestCase(TestCase):
    """Тести для RSVP моделі"""

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
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_rsvp_creation(self):
        """Тест створення RSVP"""
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        self.assertEqual(rsvp.user, self.user1)
        self.assertEqual(rsvp.event, self.event)
        self.assertEqual(rsvp.status, "going")
        self.assertIsNotNone(rsvp.created_at)

    def test_rsvp_default_status(self):
        """Тест дефолтного статусу RSVP"""
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event
            # Не вказуємо status - має використати дефолтний
        )
        
        self.assertEqual(rsvp.status, "going")

    def test_rsvp_str_method(self):
        """Тест __str__ методу RSVP"""
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        expected_str = f"RSVP({self.user1.id} -> {self.event.id})"
        self.assertEqual(str(rsvp), expected_str)

    def test_rsvp_unique_together_constraint(self):
        """Тест unique_together обмеження (user, event)"""
        # Створюємо перший RSVP
        RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        # Спроба створити другий RSVP для того ж користувача та події
        with self.assertRaises(IntegrityError):
            RSVP.objects.create(
                user=self.user1,
                event=self.event,
                status="maybe"
            )

    def test_rsvp_different_users_same_event(self):
        """Тест що різні користувачі можуть реєструватися на ту ж подію"""
        rsvp1 = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        rsvp2 = RSVP.objects.create(
            user=self.user2,
            event=self.event,
            status="going"
        )
        
        self.assertNotEqual(rsvp1.user, rsvp2.user)
        self.assertEqual(rsvp1.event, rsvp2.event)

    def test_rsvp_same_user_different_events(self):
        """Тест що той же користувач може реєструватися на різні події"""
        event2 = Event.objects.create(
            title="Another Event",
            description="Another Description",
            starts_at=timezone.now() + timedelta(days=2),
            ends_at=timezone.now() + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        rsvp1 = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        rsvp2 = RSVP.objects.create(
            user=self.user1,
            event=event2,
            status="going"
        )
        
        self.assertEqual(rsvp1.user, rsvp2.user)
        self.assertNotEqual(rsvp1.event, rsvp2.event)

    def test_rsvp_cascade_delete_user(self):
        """Тест що RSVP видаляється при видаленні користувача"""
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        rsvp_id = rsvp.id
        
        # Видаляємо користувача
        self.user1.delete()
        
        # Перевіряємо що RSVP також видалено
        self.assertFalse(RSVP.objects.filter(id=rsvp_id).exists())

    def test_rsvp_model_fields(self):
        """Тест полів RSVP моделі"""
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="maybe"
        )
        
        # Перевіряємо що всі поля встановлені правильно
        self.assertEqual(rsvp.user_id, self.user1.id)
        self.assertEqual(rsvp.event_id, self.event.id)
        self.assertEqual(rsvp.status, "maybe")
        self.assertIsNotNone(rsvp.created_at)

    def test_rsvp_related_names(self):
        """Тест related_name для зворотних зв'язків"""
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        # Перевіряємо що можна отримати RSVP через user.rsvps
        user_rsvps = self.user1.rsvps.all()
        self.assertIn(rsvp, user_rsvps)
        
        # Перевіряємо що можна отримати RSVP через event.rsvps
        event_rsvps = self.event.rsvps.all()
        self.assertIn(rsvp, event_rsvps)

    def test_rsvp_status_field_max_length(self):
        """Тест максимальної довжини поля status"""
        # Тест status max_length=20
        long_status = "a" * 20
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status=long_status
        )
        
        self.assertEqual(len(rsvp.status), 20)

    def test_rsvp_auto_now_add_created_at(self):
        """Тест що created_at автоматично встановлюється при створенні"""
        before_creation = timezone.now()
        
        rsvp = RSVP.objects.create(
            user=self.user1,
            event=self.event,
            status="going"
        )
        
        after_creation = timezone.now()
        
        # Перевіряємо що created_at встановлено між before та after
        self.assertGreaterEqual(rsvp.created_at, before_creation)
        self.assertLessEqual(rsvp.created_at, after_creation)
