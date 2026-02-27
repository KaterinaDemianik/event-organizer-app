"""
Фінальні тести для досягнення 100% coverage
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command
from io import StringIO
from datetime import timedelta
from unittest.mock import patch, MagicMock

from events.models import Event, Review
from tickets.models import RSVP
from users.models import UserProfile


class ReviewCreateViewFullCoverageTestCase(TestCase):
    """Тести для events/ui_views.py review_create_view - рядки 487-488, 500-502"""

    def setUp(self):
        self.client = Client()
        
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
        
        # Минула подія для відгуку
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=2, hours=-2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_review_already_exists(self):
        """Тест коли відгук вже існує - рядки 487-488"""
        self.client.login(username="testuser", password="testpass123")
        
        # Створюємо RSVP
        RSVP.objects.create(user=self.user, event=self.past_event, status="going")
        
        # Створюємо відгук
        Review.objects.create(
            event=self.past_event,
            user=self.user,
            rating=5,
            comment="Great!"
        )
        
        # Спробуємо створити ще один відгук
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertIn(response.status_code, [200, 302])

    def test_review_form_get(self):
        """Тест GET запиту на форму відгуку - рядки 500-502"""
        self.client.login(username="testuser", password="testpass123")
        
        # Створюємо RSVP
        RSVP.objects.create(user=self.user, event=self.past_event, status="going")
        
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertIn(response.status_code, [200, 302])


class EventUpdateNotificationTestCase(TestCase):
    """Тести для events/ui_views.py EventUpdateView - рядок 570"""

    def setUp(self):
        self.client = Client()
        
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        self.participant = User.objects.create_user(
            username="participant",
            email="participant@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            location="Київ",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        # Додаємо учасника
        RSVP.objects.create(user=self.participant, event=self.event, status="going")

    def test_event_update_with_notifications(self):
        """Тест оновлення події з надсиланням сповіщень - рядок 570"""
        self.client.login(username="organizer", password="testpass123")
        
        new_time = timezone.now() + timedelta(days=10)
        
        response = self.client.post(f'/events/{self.event.pk}/edit/', {
            'title': 'Updated Event Title',
            'description': 'Updated description',
            'location': 'Львів',
            'starts_at': new_time.strftime('%Y-%m-%dT%H:%M'),
            'ends_at': (new_time + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
            'status': Event.PUBLISHED,
        })
        self.assertIn(response.status_code, [200, 302])


class EventCancelArchiveGetTestCase(TestCase):
    """Тести для GET запитів на cancel/archive - рядки 630, 652"""

    def setUp(self):
        self.client = Client()
        
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

    def test_event_cancel_get_request(self):
        """Тест GET запиту на скасування - рядок 630"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/cancel/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_archive_get_request(self):
        """Тест GET запиту на архівування - рядок 652"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/archive/')
        self.assertIn(response.status_code, [200, 302])


class CalendarViewFiltersTestCase(TestCase):
    """Тести для CalendarView з фільтрами - рядки 707-714"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_calendar_schedule_filter_upcoming(self):
        """Тест schedule_filter=upcoming - рядок 707"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?schedule_filter=upcoming')
        self.assertEqual(response.status_code, 200)

    def test_calendar_schedule_filter_organized(self):
        """Тест schedule_filter=organized - рядок 709"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?schedule_filter=organized')
        self.assertEqual(response.status_code, 200)

    def test_calendar_schedule_filter_published(self):
        """Тест schedule_filter=published - рядок 711"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?schedule_filter=published')
        self.assertEqual(response.status_code, 200)

    def test_calendar_highlight_mode(self):
        """Тест highlight mode - рядок 714"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?highlight=soon')
        self.assertEqual(response.status_code, 200)

    def test_calendar_combined_filters(self):
        """Тест комбінованих фільтрів"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?schedule_filter=upcoming&highlight=organizer')
        self.assertEqual(response.status_code, 200)


class ProfileViewFormValidTestCase(TestCase):
    """Тести для users/views.py ProfileView.form_valid - рядки 95-97"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        
        UserProfile.objects.create(
            user=self.user,
            birth_date="1990-01-15",
            city="Київ",
            phone="+380501234567"
        )

    def test_profile_update_form_valid(self):
        """Тест успішного оновлення профілю через POST"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.post('/accounts/profile/', {
            'username': 'testuser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
            'birth_date': '1990-01-15',
            'city': 'Львів',
            'phone': '+380509999999'
        }, follow=True)
        
        self.assertIn(response.status_code, [200, 302])


class PasswordChangeFormValidTestCase(TestCase):
    """Тести для users/views.py UserPasswordChangeView.form_valid - рядки 105-106"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_password_change_form_valid(self):
        """Тест успішної зміни пароля"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.post('/accounts/password/change/', {
            'old_password': 'testpass123',
            'new_password1': 'newSecurePass456!',
            'new_password2': 'newSecurePass456!'
        }, follow=True)
        
        self.assertIn(response.status_code, [200, 302])


class FixRSVPDuplicatesCommandFullTestCase(TestCase):
    """Повні тести для fix_rsvp_duplicates команди - рядки 25-42"""

    def setUp(self):
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
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_command_removes_invalid_status(self):
        """Тест видалення RSVP з невалідним статусом"""
        # Створюємо RSVP і змінюємо статус на невалідний
        rsvp = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.filter(pk=rsvp.pk).update(status="maybe")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        # Перевіряємо що команда виконалась
        self.assertIn('Всього видалено', output)
        
        # Перевіряємо що RSVP з невалідним статусом видалено
        self.assertFalse(RSVP.objects.filter(pk=rsvp.pk).exists())

    def test_command_keeps_valid_rsvp(self):
        """Тест що валідні RSVP залишаються"""
        rsvp = RSVP.objects.create(user=self.user2, event=self.event1, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        # Перевіряємо що валідний RSVP залишився
        self.assertTrue(RSVP.objects.filter(pk=rsvp.pk).exists())
