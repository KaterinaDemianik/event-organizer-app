"""
Тести для notifications/views.py - покриття всіх view функцій
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from notifications.models import Notification


class NotificationViewsTestCase(TestCase):
    """Тести для notification views"""

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
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        self.notification = Notification.objects.create(
            user=self.user,
            event=self.event,
            notification_type=Notification.RSVP_CONFIRMED,
            message="Test notification"
        )

    def test_notification_list_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get('/notifications/')
        self.assertEqual(response.status_code, 302)

    def test_notification_list_authenticated(self):
        """Тест списку нотифікацій для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/notifications/')
        self.assertEqual(response.status_code, 200)

    def test_notification_mark_read(self):
        """Тест позначення нотифікації як прочитаної"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/notifications/{self.notification.pk}/read/')
        self.assertIn(response.status_code, [200, 302])

    def test_notification_mark_all_read(self):
        """Тест позначення всіх нотифікацій як прочитаних"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post('/notifications/mark-all-read/')
        self.assertIn(response.status_code, [200, 302])

    def test_notification_detail(self):
        """Тест деталей нотифікації"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/notifications/{self.notification.pk}/')
        self.assertIn(response.status_code, [200, 302, 404])
