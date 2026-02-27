"""
Додаткові тести для досягнення 100% coverage
Покриває залишкові непокриті рядки
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F, Count

from events.models import Event
from tickets.models import RSVP
from users.models import UserProfile
from users.forms import UserProfileForm


class EventListViewFullCoverageTestCase(TestCase):
    """Тести для events/ui_views.py EventListView - рядки 273-349"""

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
        
        now = timezone.now()
        
        # Створюємо події для різних фільтрів
        self.published_event = Event.objects.create(
            title="Published Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED,
            capacity=10
        )
        
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Description",
            starts_at=now - timedelta(days=10),
            ends_at=now - timedelta(days=10, hours=-2),
            organizer=self.user,
            status=Event.ARCHIVED
        )
        
        self.full_event = Event.objects.create(
            title="Full Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED,
            capacity=1
        )
        
        # Додаємо RSVP щоб подія була повна
        RSVP.objects.create(user=self.staff_user, event=self.full_event, status="going")

    def test_event_list_view_my(self):
        """Тест view=my фільтру"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/events/?view=my')
        self.assertEqual(response.status_code, 200)

    def test_event_list_view_upcoming(self):
        """Тест view=upcoming фільтру"""
        self.client.login(username="testuser", password="testpass123")
        # Додаємо RSVP для користувача
        RSVP.objects.create(user=self.user, event=self.published_event, status="going")
        response = self.client.get('/events/?view=upcoming')
        self.assertEqual(response.status_code, 200)

    def test_event_list_view_archived_staff(self):
        """Тест view=archived для staff"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/events/?view=archived')
        self.assertEqual(response.status_code, 200)

    def test_event_list_view_archived_regular_user(self):
        """Тест view=archived для звичайного користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/events/?view=archived')
        self.assertEqual(response.status_code, 200)

    def test_event_list_date_filter_upcoming(self):
        """Тест date_filter=upcoming"""
        response = self.client.get('/events/?date_filter=upcoming')
        self.assertEqual(response.status_code, 200)

    def test_event_list_date_filter_today(self):
        """Тест date_filter=today"""
        response = self.client.get('/events/?date_filter=today')
        self.assertEqual(response.status_code, 200)

    def test_event_list_date_filter_this_week(self):
        """Тест date_filter=this_week"""
        response = self.client.get('/events/?date_filter=this_week')
        self.assertEqual(response.status_code, 200)

    def test_event_list_date_filter_this_month(self):
        """Тест date_filter=this_month"""
        response = self.client.get('/events/?date_filter=this_month')
        self.assertEqual(response.status_code, 200)

    def test_event_list_popularity_popular(self):
        """Тест popularity=popular"""
        response = self.client.get('/events/?popularity=popular')
        self.assertEqual(response.status_code, 200)

    def test_event_list_popularity_medium(self):
        """Тест popularity=medium"""
        response = self.client.get('/events/?popularity=medium')
        self.assertEqual(response.status_code, 200)

    def test_event_list_popularity_none(self):
        """Тест popularity=none"""
        response = self.client.get('/events/?popularity=none')
        self.assertEqual(response.status_code, 200)

    def test_event_list_availability_available(self):
        """Тест availability=available"""
        response = self.client.get('/events/?availability=available')
        self.assertEqual(response.status_code, 200)

    def test_event_list_availability_full(self):
        """Тест availability=full"""
        response = self.client.get('/events/?availability=full')
        self.assertEqual(response.status_code, 200)


class UserProfileFormFullCoverageTestCase(TestCase):
    """Тести для users/forms.py - рядки 92-99"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_user_profile_form_save_creates_profile(self):
        """Тест що save створює профіль якщо його немає"""
        form = UserProfileForm(instance=self.user, data={
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'birth_date': '1990-01-01',
            'city': 'Київ',
            'phone': '+380501234567'
        })
        
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.city, 'Київ')

    def test_user_profile_form_save_with_existing_profile(self):
        """Тест що save оновлює існуючий профіль"""
        UserProfile.objects.create(
            user=self.user,
            birth_date="1985-05-05",
            city="Одеса",
            phone="+380501111111"
        )
        
        form = UserProfileForm(instance=self.user, data={
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'birth_date': '1990-01-01',
            'city': 'Львів',
            'phone': '+380502222222'
        })
        
        self.assertTrue(form.is_valid())
        user = form.save()
        
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.city, 'Львів')

    def test_user_profile_form_init_with_profile(self):
        """Тест ініціалізації форми з існуючим профілем"""
        UserProfile.objects.create(
            user=self.user,
            birth_date="1990-06-15",
            city="Харків",
            phone="+380503333333"
        )
        
        form = UserProfileForm(instance=self.user)
        
        self.assertEqual(form.fields['city'].initial, 'Харків')
        self.assertEqual(form.fields['phone'].initial, '+380503333333')


class UIViewsRemainingCoverageTestCase(TestCase):
    """Тести для events/ui_views.py - залишкові рядки 487-735"""

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
        
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=1),
            ends_at=now - timedelta(hours=22),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_event_update_view_get(self):
        """Тест GET запиту на редагування події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/edit/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_cancel_view(self):
        """Тест скасування події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/cancel/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_archive_view(self):
        """Тест архівування події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.past_event.pk}/archive/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_participants_view(self):
        """Тест перегляду учасників"""
        self.client.login(username="organizer", password="testpass123")
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        response = self.client.get(f'/events/{self.event.pk}/participants/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_create(self):
        """Тест створення RSVP"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_cancel(self):
        """Тест скасування RSVP"""
        self.client.login(username="testuser", password="testpass123")
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        response = self.client.post(f'/events/{self.event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_review_create_view(self):
        """Тест створення відгуку"""
        self.client.login(username="testuser", password="testpass123")
        # Спочатку реєструємось на подію
        RSVP.objects.create(user=self.user, event=self.past_event, status="going")
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertIn(response.status_code, [200, 302])

    def test_calendar_view(self):
        """Тест календаря"""
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_authenticated(self):
        """Тест календаря для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)


class TicketsFixRSVPDuplicatesFullTestCase(TestCase):
    """Тести для tickets/management/commands/fix_rsvp_duplicates.py - рядки 25-42"""

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
        
        self.event2 = Event.objects.create(
            title="Event 2",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_command_with_invalid_status_rsvps(self):
        """Тест команди з RSVP з невалідним статусом"""
        from django.core.management import call_command
        from io import StringIO
        
        # Створюємо RSVP з невалідним статусом
        rsvp = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.filter(pk=rsvp.pk).update(status="invalid_status")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Всього видалено', output)

    def test_command_no_duplicates(self):
        """Тест команди без дублікатів"""
        from django.core.management import call_command
        from io import StringIO
        
        RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.create(user=self.user2, event=self.event2, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Всього видалено', output)
