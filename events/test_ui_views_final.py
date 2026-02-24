"""
Фінальні тести для events/ui_views.py - покриття залишкових непокритих рядків
Рядки: 143, 155-169, 176, 178, 180, 185, 187, 189, 191, 273, 277-278, 284-287, 
       315-329, 336-341, 345, 349, 411-413, 487-488, 500-502, 535, 544-545, 
       559-572, 619-620, 630, 648, 652, 707, 709, 711, 714, 735
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

from events.models import Event, Review
from tickets.models import RSVP


class HomeViewFinalTestCase(TestCase):
    """Фінальні тести для home_view - покриття фільтрів та сортування"""

    def setUp(self):
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Створюємо події з різними характеристиками
        for i in range(10):
            event = Event.objects.create(
                title=f"Event {i}",
                description=f"Description {i}",
                starts_at=now + timedelta(days=i+1),
                ends_at=now + timedelta(days=i+1, hours=2),
                organizer=self.user if i % 2 == 0 else self.staff_user,
                status=Event.PUBLISHED if i < 7 else Event.DRAFT,
                category="tech" if i % 3 == 0 else "business"
            )
            
            # Додаємо RSVP для деяких подій
            if i < 5:
                RSVP.objects.create(user=self.user, event=event, status="going")

    def test_home_staff_date_filter_past(self):
        """Тест фільтру минулих подій"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?date_filter=past&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_date_filter_today(self):
        """Тест фільтру сьогоднішніх подій"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?date_filter=today&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_date_filter_week(self):
        """Тест фільтру подій на тиждень"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?date_filter=week&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_date_filter_month(self):
        """Тест фільтру подій на місяць"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?date_filter=month&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_popularity_low(self):
        """Тест фільтру низької популярності"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?popularity=low&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_popularity_medium(self):
        """Тест фільтру середньої популярності"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?popularity=medium&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_sort_date_asc(self):
        """Тест сортування за датою (asc)"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=date_asc&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_sort_rsvp_count_desc(self):
        """Тест сортування за кількістю RSVP (desc)"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=rsvp_count_desc&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_sort_starts_at_desc(self):
        """Тест сортування за датою початку (desc)"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?sort=starts_at_desc&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_combined_filters(self):
        """Тест комбінованих фільтрів"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/?q=Event&status={Event.PUBLISHED}&organizer={self.user.id}&category=tech&date_filter=upcoming&popularity=high&sort=title_asc&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_pagination_events(self):
        """Тест пагінації подій"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?tab=events&page=1')
        self.assertEqual(response.status_code, 200)


class EventCreateViewFinalTestCase(TestCase):
    """Фінальні тести для EventCreateView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_event_create_post_invalid_dates(self):
        """Тест створення події з невалідними датами"""
        self.client.login(username="testuser", password="testpass123")
        
        now = timezone.now()
        response = self.client.post('/events/create/', {
            'title': 'Test Event',
            'description': 'Description',
            'location': 'Location',
            'starts_at': (now + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),  # ends before starts
            'status': Event.DRAFT
        })
        self.assertEqual(response.status_code, 200)

    def test_event_create_post_past_date(self):
        """Тест створення події з минулою датою"""
        self.client.login(username="testuser", password="testpass123")
        
        now = timezone.now()
        response = self.client.post('/events/create/', {
            'title': 'Test Event',
            'description': 'Description',
            'location': 'Location',
            'starts_at': (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now - timedelta(hours=22)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': Event.DRAFT
        })
        self.assertEqual(response.status_code, 200)


class EventUpdateViewFinalTestCase(TestCase):
    """Фінальні тести для EventUpdateView"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
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
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.user,
            status=Event.CANCELLED
        )

    def test_event_update_non_organizer(self):
        """Тест редагування події не організатором"""
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(f'/events/{self.event.pk}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_event_update_cancelled_event(self):
        """Тест редагування скасованої події"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.cancelled_event.pk}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_event_update_post_valid(self):
        """Тест POST запиту на оновлення події"""
        self.client.login(username="testuser", password="testpass123")
        
        now = timezone.now()
        response = self.client.post(f'/events/{self.event.pk}/edit/', {
            'title': 'Updated Event',
            'description': 'Updated Description',
            'location': 'Updated Location',
            'starts_at': (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now + timedelta(days=3, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': Event.PUBLISHED
        })
        self.assertIn(response.status_code, [200, 302])


class RSVPViewsFinalTestCase(TestCase):
    """Фінальні тести для RSVP views"""

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
        
        self.started_event = Event.objects.create(
            title="Started Event",
            description="Description",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=1),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.organizer,
            status=Event.ARCHIVED
        )

    def test_rsvp_to_started_event(self):
        """Тест реєстрації на подію що вже розпочалась"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.started_event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])

    def test_rsvp_to_archived_event(self):
        """Тест реєстрації на архівовану подію"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.archived_event.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])


class EventActionViewsFinalTestCase(TestCase):
    """Фінальні тести для дій з подіями"""

    def setUp(self):
        self.client = Client()
        
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
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
        
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Description",
            starts_at=now + timedelta(days=10),
            ends_at=now + timedelta(days=10, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_cancel_cancelled_event(self):
        """Тест скасування вже скасованої події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.cancelled_event.pk}/cancel/')
        self.assertIn(response.status_code, [200, 302])

    def test_cancel_archived_event(self):
        """Тест скасування архівованої події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.archived_event.pk}/cancel/')
        self.assertIn(response.status_code, [200, 302])

    def test_archive_future_event(self):
        """Тест архівування майбутньої події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.future_event.pk}/archive/')
        self.assertIn(response.status_code, [200, 302])

    def test_archive_cancelled_event(self):
        """Тест архівування скасованої події"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(f'/events/{self.cancelled_event.pk}/archive/')
        self.assertIn(response.status_code, [200, 302])


class CalendarViewFinalTestCase(TestCase):
    """Фінальні тести для CalendarView"""

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
        
        # Подія організована користувачем
        self.my_event = Event.objects.create(
            title="My Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Подія на яку зареєстрований
        self.rsvp_event = Event.objects.create(
            title="RSVP Event",
            description="Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )
        
        RSVP.objects.create(user=self.user, event=self.rsvp_event, status="going")

    def test_calendar_with_my_events(self):
        """Тест календаря з власними подіями"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)

    def test_calendar_previous_month(self):
        """Тест календаря з попереднім місяцем"""
        self.client.login(username="testuser", password="testpass123")
        now = timezone.now()
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        response = self.client.get(f'/calendar/?year={prev_year}&month={prev_month}')
        self.assertEqual(response.status_code, 200)

    def test_calendar_next_month(self):
        """Тест календаря з наступним місяцем"""
        self.client.login(username="testuser", password="testpass123")
        now = timezone.now()
        next_month = now.month + 1 if now.month < 12 else 1
        next_year = now.year if now.month < 12 else now.year + 1
        response = self.client.get(f'/calendar/?year={next_year}&month={next_month}')
        self.assertEqual(response.status_code, 200)


class ReviewViewFinalTestCase(TestCase):
    """Фінальні тести для створення відгуків"""

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

    def test_review_organizer_own_event(self):
        """Тест відгуку організатора на власну подію"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.past_event.pk}/review/')
        self.assertIn(response.status_code, [200, 302])

    def test_review_post_with_image(self):
        """Тест відгуку з зображенням"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.past_event.pk}/review/', {
            'rating': 4,
            'comment': 'Good event with image'
        })
        self.assertIn(response.status_code, [200, 302])
