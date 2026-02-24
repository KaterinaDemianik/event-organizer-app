"""
Розширені тести для events/ui_views.py - покриття залишкових непокритих рядків
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta, date

from events.models import Event, Review
from tickets.models import RSVP


class HomeViewExtendedTestCase(TestCase):
    """Розширені тести для home_view"""

    def setUp(self):
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
        now = timezone.now()
        
        for i in range(5):
            Event.objects.create(
                title=f"Event {i}",
                description=f"Description {i}",
                starts_at=now + timedelta(days=i+1),
                ends_at=now + timedelta(days=i+1, hours=2),
                organizer=self.staff_user,
                status=Event.PUBLISHED,
                category="tech"
            )

    def test_home_view_staff_tab_events(self):
        """Тест адмін панелі з табом events"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_tab_users(self):
        """Тест адмін панелі з табом users"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?tab=users')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_search(self):
        """Тест адмін панелі з пошуком"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?q=Event&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_organizer_filter(self):
        """Тест адмін панелі з фільтром організатора"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/?organizer={self.staff_user.id}&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_category_filter(self):
        """Тест адмін панелі з фільтром категорії"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?category=tech&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_date_filter(self):
        """Тест адмін панелі з фільтром дати"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?date_filter=upcoming&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_with_popularity_filter(self):
        """Тест адмін панелі з фільтром популярності"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?popularity=high&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_sort_title_asc(self):
        """Тест адмін панелі з сортуванням за назвою"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=title_asc&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_sort_title_desc(self):
        """Тест адмін панелі з сортуванням за назвою (desc)"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=title_desc&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_sort_rsvp_count(self):
        """Тест адмін панелі з сортуванням за кількістю RSVP"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=rsvp_count&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_sort_starts_at(self):
        """Тест адмін панелі з сортуванням за датою початку"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=starts_at&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_pagination(self):
        """Тест пагінації в адмін панелі"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?tab=events&page=1')
        self.assertEqual(response.status_code, 200)


class EventListViewExtendedTestCase(TestCase):
    """Розширені тести для EventListView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        for i in range(15):
            Event.objects.create(
                title=f"Event {i}",
                description=f"Description {i}",
                starts_at=now + timedelta(days=i+1),
                ends_at=now + timedelta(days=i+1, hours=2),
                organizer=self.user,
                status=Event.PUBLISHED,
                location="Київ",
                category="tech"
            )

    def test_event_list_with_date_range(self):
        """Тест списку подій з діапазоном дат"""
        today = date.today()
        date_from = today.strftime('%Y-%m-%d')
        date_to = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        response = self.client.get(f'/events/?date_from={date_from}&date_to={date_to}')
        self.assertEqual(response.status_code, 200)

    def test_event_list_sort_date_asc(self):
        """Тест сортування за датою (asc)"""
        response = self.client.get('/events/?sort=date_asc')
        self.assertEqual(response.status_code, 200)

    def test_event_list_sort_date_desc(self):
        """Тест сортування за датою (desc)"""
        response = self.client.get('/events/?sort=date_desc')
        self.assertEqual(response.status_code, 200)

    def test_event_list_multiple_filters(self):
        """Тест списку подій з кількома фільтрами"""
        response = self.client.get('/events/?q=Event&status=published&location=Київ&category=tech')
        self.assertEqual(response.status_code, 200)


class EventDetailViewExtendedTestCase(TestCase):
    """Розширені тести для EventDetailView"""

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
            status=Event.PUBLISHED,
            capacity=10
        )
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.CANCELLED
        )
        
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.organizer,
            status=Event.ARCHIVED
        )

    def test_event_detail_cancelled(self):
        """Тест детальної сторінки скасованої події"""
        response = self.client.get(f'/events/{self.cancelled_event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_archived(self):
        """Тест детальної сторінки архівованої події"""
        response = self.client.get(f'/events/{self.archived_event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_organizer_view(self):
        """Тест детальної сторінки для організатора"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_with_reviews(self):
        """Тест детальної сторінки з відгуками"""
        Review.objects.create(
            event=self.archived_event,
            user=self.user,
            rating=5,
            comment="Great event!"
        )
        
        response = self.client.get(f'/events/{self.archived_event.pk}/')
        self.assertEqual(response.status_code, 200)


class RSVPViewsExtendedTestCase(TestCase):
    """Розширені тести для RSVP views"""

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
            status=Event.PUBLISHED,
            capacity=10
        )
        
        self.full_event = Event.objects.create(
            title="Full Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED,
            capacity=1
        )
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=2),
            organizer=self.organizer,
            status=Event.CANCELLED
        )

    def test_rsvp_to_full_event(self):
        """Тест реєстрації на повну подію"""
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123"
        )
        RSVP.objects.create(user=other_user, event=self.full_event, status="going")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.full_event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_to_cancelled_event(self):
        """Тест реєстрації на скасовану подію"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.cancelled_event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_already_registered(self):
        """Тест повторної реєстрації"""
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_cancel_not_registered(self):
        """Тест скасування реєстрації коли не зареєстрований"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/rsvp/cancel/')
        self.assertIn(response.status_code, [200, 302])


class EventActionViewsExtendedTestCase(TestCase):
    """Розширені тести для дій з подіями"""

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
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )

    def test_event_cancel_non_organizer(self):
        """Тест скасування події не організатором"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/cancel/')
        self.assertEqual(response.status_code, 302)

    def test_event_cancel_staff(self):
        """Тест скасування події staff"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/cancel/')
        self.assertIn(response.status_code, [200, 302])

    def test_event_archive_non_organizer(self):
        """Тест архівування події не організатором"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event.pk}/archive/')
        self.assertEqual(response.status_code, 302)

    def test_event_participants_non_organizer(self):
        """Тест перегляду учасників не організатором"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/participants/')
        self.assertEqual(response.status_code, 302)

    def test_event_participants_staff(self):
        """Тест перегляду учасників staff"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/participants/')
        self.assertEqual(response.status_code, 200)


class CalendarViewExtendedTestCase(TestCase):
    """Розширені тести для CalendarView"""

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
        
        RSVP.objects.create(user=self.user, event=self.event, status="going")

    def test_calendar_with_events(self):
        """Тест календаря з подіями"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)

    def test_calendar_different_months(self):
        """Тест календаря з різними місяцями"""
        self.client.login(username="testuser", password="testpass123")
        
        for month in range(1, 13):
            response = self.client.get(f'/calendar/?year=2026&month={month}')
            self.assertEqual(response.status_code, 200)

    def test_calendar_invalid_params(self):
        """Тест календаря з невалідними параметрами"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/?year=invalid&month=invalid')
        self.assertIn(response.status_code, [200, 400])


class ReviewViewExtendedTestCase(TestCase):
    """Розширені тести для створення відгуків"""

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
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now - timedelta(days=3),
            ends_at=now - timedelta(days=2),
            organizer=self.organizer,
            status=Event.CANCELLED
        )

    def test_review_cancelled_event(self):
        """Тест відгуку на скасовану подію"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.cancelled_event.pk}/review/')
        self.assertIn(response.status_code, [200, 302])

    def test_review_post_invalid_rating(self):
        """Тест відгуку з невалідним рейтингом"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.past_event.pk}/review/', {
            'rating': 10,
            'comment': 'Invalid rating'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_review_post_empty_comment(self):
        """Тест відгуку з порожнім коментарем"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.past_event.pk}/review/', {
            'rating': 5,
            'comment': ''
        })
        self.assertIn(response.status_code, [200, 302])
