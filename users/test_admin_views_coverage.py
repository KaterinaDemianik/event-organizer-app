"""
Тести для users/admin_views.py - покриття адмін view функцій
Примітка: admin_views функції не підключені до URL, тому тестуємо їх напряму
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from tickets.models import RSVP
from users.admin_views import admin_dashboard, admin_events_list, admin_users_list, admin_rsvps_list


class AdminDashboardViewTestCase(TestCase):
    """Тести для admin_dashboard"""

    def setUp(self):
        self.factory = RequestFactory()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_admin_dashboard_staff_access(self):
        """Тест доступу staff до дашборду"""
        request = self.factory.get('/admin-dashboard/')
        request.user = self.staff_user
        
        response = admin_dashboard(request)
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_with_data(self):
        """Тест дашборду з даними"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        request = self.factory.get('/admin-dashboard/')
        request.user = self.staff_user
        
        response = admin_dashboard(request)
        self.assertEqual(response.status_code, 200)


class AdminEventsListViewTestCase(TestCase):
    """Тести для admin_events_list"""

    def setUp(self):
        self.factory = RequestFactory()
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.staff_user,
            status=Event.PUBLISHED
        )

    def test_admin_events_list_staff_access(self):
        """Тест доступу staff до списку подій"""
        request = self.factory.get('/admin-events/')
        request.user = self.staff_user
        
        response = admin_events_list(request)
        self.assertEqual(response.status_code, 200)

    def test_admin_events_list_with_status_filter(self):
        """Тест списку подій з фільтром статусу"""
        request = self.factory.get(f'/admin-events/?status={Event.PUBLISHED}')
        request.user = self.staff_user
        
        response = admin_events_list(request)
        self.assertEqual(response.status_code, 200)


class AdminUsersListViewTestCase(TestCase):
    """Тести для admin_users_list"""

    def setUp(self):
        self.factory = RequestFactory()
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )

    def test_admin_users_list_staff_access(self):
        """Тест доступу staff до списку користувачів"""
        request = self.factory.get('/admin-users/')
        request.user = self.staff_user
        
        response = admin_users_list(request)
        self.assertEqual(response.status_code, 200)


class AdminRSVPsListViewTestCase(TestCase):
    """Тести для admin_rsvps_list"""

    def setUp(self):
        self.factory = RequestFactory()
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.staff_user,
            status=Event.PUBLISHED
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        RSVP.objects.create(user=self.user, event=self.event, status="going")

    def test_admin_rsvps_list_staff_access(self):
        """Тест доступу staff до списку RSVP"""
        request = self.factory.get('/admin-rsvps/')
        request.user = self.staff_user
        
        response = admin_rsvps_list(request)
        self.assertEqual(response.status_code, 200)
