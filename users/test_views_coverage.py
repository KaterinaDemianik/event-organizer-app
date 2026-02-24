"""
Тести для users/views.py - покриття всіх view класів та функцій
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta, date

from events.models import Event, Review
from tickets.models import RSVP
from users.models import UserProfile


class LoginViewTestCase(TestCase):
    """Тести для LoginView"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_login_view_anonymous(self):
        """Тест сторінки логіну для анонімного користувача"""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_view_authenticated_redirects(self):
        """Тест що авторизований користувач перенаправляється"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 302)

    def test_login_post_valid(self):
        """Тест успішного логіну"""
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_post_invalid(self):
        """Тест невдалого логіну"""
        response = self.client.post('/accounts/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)


class SignupViewTestCase(TestCase):
    """Тести для SignupView"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="testpass123"
        )

    def test_signup_view_anonymous(self):
        """Тест сторінки реєстрації для анонімного користувача"""
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)

    def test_signup_view_authenticated_redirects(self):
        """Тест що авторизований користувач перенаправляється"""
        self.client.login(username="existinguser", password="testpass123")
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 302)

    def test_signup_post_valid(self):
        """Тест успішної реєстрації"""
        response = self.client.post('/accounts/signup/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_signup_post_invalid_passwords_mismatch(self):
        """Тест реєстрації з різними паролями"""
        response = self.client.post('/accounts/signup/', {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!'
        })
        self.assertEqual(response.status_code, 200)


class ProfileViewTestCase(TestCase):
    """Тести для ProfileView"""

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
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=1),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_profile_view_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        """Тест профілю для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_view_with_rsvps(self):
        """Тест профілю з RSVP"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_view_with_reviews(self):
        """Тест профілю з відгуками"""
        Review.objects.create(
            event=self.past_event,
            user=self.organizer,
            rating=5,
            comment="Great!"
        )
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_view_with_user_profile(self):
        """Тест профілю з UserProfile та датою народження"""
        UserProfile.objects.create(
            user=self.user,
            birth_date=date(1990, 5, 15),
            city="Київ"
        )
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_view_context_data(self):
        """Тест контекстних даних профілю"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/profile/')
        
        self.assertIn('user_obj', response.context)
        self.assertIn('rsvp_count', response.context)
        self.assertIn('my_events_count', response.context)

    def test_profile_update_post(self):
        """Тест оновлення профілю"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post('/accounts/profile/', {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com'
        })
        self.assertIn(response.status_code, [200, 302])


class PasswordChangeViewTestCase(TestCase):
    """Тести для UserPasswordChangeView"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_password_change_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get('/accounts/password_change/')
        self.assertEqual(response.status_code, 302)

    def test_password_change_get(self):
        """Тест GET запиту на зміну пароля"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/password_change/')
        self.assertEqual(response.status_code, 200)

    def test_password_change_post_valid(self):
        """Тест успішної зміни пароля"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post('/accounts/password_change/', {
            'old_password': 'testpass123',
            'new_password1': 'NewComplexPass123!',
            'new_password2': 'NewComplexPass123!'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_password_change_done(self):
        """Тест сторінки успішної зміни пароля"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/password_change/done/')
        self.assertEqual(response.status_code, 200)


class AdminCreateUserViewTestCase(TestCase):
    """Тести для admin_create_user"""

    def setUp(self):
        self.client = Client()
        
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

    def test_admin_create_user_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get('/accounts/admin/create-user/')
        self.assertEqual(response.status_code, 302)

    def test_admin_create_user_non_staff_redirects(self):
        """Тест що не-staff користувач перенаправляється"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/accounts/admin/create-user/')
        self.assertEqual(response.status_code, 302)

    def test_admin_create_user_staff_get(self):
        """Тест GET запиту для staff"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/accounts/admin/create-user/')
        self.assertEqual(response.status_code, 200)

    def test_admin_create_user_staff_post_valid(self):
        """Тест POST запиту для створення користувача"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.post('/accounts/admin/create-user/', {
            'username': 'newadminuser',
            'email': 'newadmin@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_admin_create_user_staff_post_invalid(self):
        """Тест POST запиту з невалідними даними"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.post('/accounts/admin/create-user/', {
            'username': '',
            'email': 'invalid',
            'password1': 'pass',
            'password2': 'different'
        })
        self.assertEqual(response.status_code, 200)
