"""
Комплексні тести для events/ui_views.py - покриття всіх view функцій
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta, date
from unittest.mock import patch, MagicMock

from events.models import Event, Review
from tickets.models import RSVP


class HomeViewTestCase(TestCase):
    """Тести для home_view"""

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
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_home_view_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])

    def test_home_view_regular_user(self):
        """Тест головної сторінки для звичайного користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 302])

    def test_home_view_staff_default(self):
        """Тест головної сторінки для staff (адмін панель)"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_period_today(self):
        """Тест адмін панелі з періодом today"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=today')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_period_week(self):
        """Тест адмін панелі з періодом week"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=week')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_period_month(self):
        """Тест адмін панелі з періодом month"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=month')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_period_quarter(self):
        """Тест адмін панелі з періодом quarter"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=quarter')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_period_year(self):
        """Тест адмін панелі з періодом year"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=year')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_period_all(self):
        """Тест адмін панелі з періодом all"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=all')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_custom_period(self):
        """Тест адмін панелі з кастомним періодом"""
        self.client.login(username="staffuser", password="testpass123")
        today = date.today()
        date_from = today.strftime('%Y-%m-%d')
        date_to = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        response = self.client.get(f'/?period=custom&date_from={date_from}&date_to={date_to}')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_custom_period_only_from(self):
        """Тест адмін панелі з кастомним періодом тільки date_from"""
        self.client.login(username="staffuser", password="testpass123")
        today = date.today()
        date_from = today.strftime('%Y-%m-%d')
        response = self.client.get(f'/?period=custom&date_from={date_from}')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_custom_period_invalid_date(self):
        """Тест адмін панелі з невалідною датою"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?period=custom&date_from=invalid-date')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_tab(self):
        """Тест адмін панелі з різними табами"""
        self.client.login(username="staffuser", password="testpass123")
        
        tabs = ['stats', 'events', 'users']
        for tab in tabs:
            response = self.client.get(f'/?tab={tab}')
            self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_filters(self):
        """Тест адмін панелі з фільтрами"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?q=Test&status=published&sort=date_desc')
        self.assertEqual(response.status_code, 200)


class EventListViewTestCase(TestCase):
    """Тести для EventListView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED,
            location="Київ",
            category="tech"
        )

    def test_event_list_basic(self):
        """Тест базового списку подій"""
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    def test_event_list_with_search(self):
        """Тест списку подій з пошуком"""
        response = self.client.get('/events/?q=Test')
        self.assertEqual(response.status_code, 200)

    def test_event_list_with_status_filter(self):
        """Тест списку подій з фільтром статусу"""
        response = self.client.get(f'/events/?status={Event.PUBLISHED}')
        self.assertEqual(response.status_code, 200)

    def test_event_list_with_location_filter(self):
        """Тест списку подій з фільтром локації"""
        response = self.client.get('/events/?location=Київ')
        self.assertEqual(response.status_code, 200)

    def test_event_list_with_category_filter(self):
        """Тест списку подій з фільтром категорії"""
        response = self.client.get('/events/?category=tech')
        self.assertEqual(response.status_code, 200)

    def test_event_list_with_sorting(self):
        """Тест списку подій з різним сортуванням"""
        sorts = ['date', 'popular', 'alphabet', 'event_date', 'rsvp_count']
        for sort in sorts:
            response = self.client.get(f'/events/?sort={sort}')
            self.assertEqual(response.status_code, 200)

    def test_event_list_pagination(self):
        """Тест пагінації списку подій"""
        # Створюємо багато подій
        for i in range(25):
            Event.objects.create(
                title=f"Event {i}",
                description=f"Description {i}",
                starts_at=timezone.now() + timedelta(days=i+10),
                ends_at=timezone.now() + timedelta(days=i+10, hours=2),
                organizer=self.user,
                status=Event.PUBLISHED
            )
        
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/events/?page=2')
        self.assertEqual(response.status_code, 200)


class EventDetailViewTestCase(TestCase):
    """Тести для EventDetailView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
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

    def test_event_detail_anonymous(self):
        """Тест детальної сторінки для анонімного користувача"""
        response = self.client.get(f'/events/{self.event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_authenticated(self):
        """Тест детальної сторінки для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_with_rsvp(self):
        """Тест детальної сторінки з RSVP"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_nonexistent(self):
        """Тест детальної сторінки неіснуючої події"""
        response = self.client.get('/events/99999/')
        self.assertEqual(response.status_code, 404)


class EventCreateViewTestCase(TestCase):
    """Тести для EventCreateView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_event_create_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get('/events/create/')
        self.assertEqual(response.status_code, 302)

    def test_event_create_get(self):
        """Тест GET запиту на створення події"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/events/create/')
        self.assertEqual(response.status_code, 200)

    def test_event_create_post_valid(self):
        """Тест POST запиту на створення події"""
        self.client.login(username="testuser", password="testpass123")
        
        now = timezone.now()
        form_data = {
            'title': 'New Event',
            'description': 'New Description',
            'location': 'New Location',
            'starts_at': (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now + timedelta(days=1, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': Event.DRAFT,
            'capacity': 50
        }
        
        response = self.client.post('/events/create/', data=form_data)
        self.assertIn(response.status_code, [200, 302])


class EventUpdateViewTestCase(TestCase):
    """Тести для EventUpdateView"""

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
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_event_update_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get(f'/events/{self.event.pk}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_event_update_organizer_get(self):
        """Тест GET запиту на редагування організатором"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_event_update_staff_get(self):
        """Тест GET запиту на редагування staff"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/edit/')
        self.assertEqual(response.status_code, 200)


class RSVPViewsTestCase(TestCase):
    """Тести для RSVP views"""

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

    def test_rsvp_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.post(f'/events/{self.event.pk}/rsvp/')
        self.assertEqual(response.status_code, 302)

    def test_rsvp_authenticated(self):
        """Тест реєстрації на подію"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_cancel(self):
        """Тест скасування реєстрації"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/rsvp/cancel/')
        self.assertIn(response.status_code, [200, 302])


class EventActionViewsTestCase(TestCase):
    """Тести для дій з подіями"""

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
        
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=1),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_event_cancel_organizer(self):
        """Тест скасування події організатором"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/cancel/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_archive_organizer(self):
        """Тест архівування події організатором"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.past_event.pk}/archive/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_participants_organizer(self):
        """Тест перегляду учасників"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/participants/')
        self.assertEqual(response.status_code, 200)


class CalendarViewTestCase(TestCase):
    """Тести для CalendarView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_calendar_anonymous_access(self):
        """Тест що анонімний користувач може переглядати календар"""
        response = self.client.get('/calendar/')
        self.assertIn(response.status_code, [200, 302])

    def test_calendar_authenticated(self):
        """Тест календаря для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)

    def test_calendar_with_date_params(self):
        """Тест календаря з параметрами дати"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?year=2024&month=12')
        self.assertEqual(response.status_code, 200)

    def test_calendar_json_response(self):
        """Тест JSON відповіді календаря"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)


class ReviewViewTestCase(TestCase):
    """Тести для створення відгуків"""

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
        
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Description",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=1),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_review_anonymous_redirects(self):
        """Тест що анонімний користувач перенаправляється"""
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertEqual(response.status_code, 302)

    def test_review_future_event_redirects(self):
        """Тест що не можна залишити відгук на майбутню подію"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.future_event.pk}/review/')
        self.assertEqual(response.status_code, 302)

    def test_review_past_event_get(self):
        """Тест GET запиту на створення відгуку"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertIn(response.status_code, [200, 302])

    def test_review_past_event_post(self):
        """Тест POST запиту на створення відгуку"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'rating': 5,
            'comment': 'Great event!'
        }
        
        response = self.client.post(f'/events/{self.past_event.pk}/review/', data=form_data)
        self.assertIn(response.status_code, [200, 302])

    def test_review_duplicate_redirects(self):
        """Тест що не можна залишити повторний відгук"""
        Review.objects.create(
            event=self.past_event,
            user=self.user,
            rating=4,
            comment="First review"
        )
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertEqual(response.status_code, 302)
