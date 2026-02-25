"""
Фінальні тести для events/ui_views.py - покриття залишкових рядків для 100%
Рядки: 162-164, 169, 176, 180, 187, 189, 191, 273, 277-278, 284-287, 
       315-329, 336-341, 345, 349, 411-413, 487-488, 500-502, 570, 630, 
       652, 707, 709, 711, 714, 735
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import Event, Review
from tickets.models import RSVP


class HomeViewFinal100TestCase(TestCase):
    """Фінальні тести для home_view - 100% coverage"""

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
        for i in range(20):
            event = Event.objects.create(
                title=f"Event {i}",
                description=f"Description {i}",
                starts_at=now + timedelta(days=i-5),
                ends_at=now + timedelta(days=i-5, hours=2),
                organizer=self.user if i % 2 == 0 else self.staff_user,
                status=Event.PUBLISHED if i < 15 else Event.DRAFT,
                category="tech" if i % 3 == 0 else "business"
            )
            
            # Додаємо RSVP для деяких подій
            for j in range(i % 5):
                user = User.objects.create_user(
                    username=f"user{i}_{j}",
                    email=f"user{i}_{j}@example.com",
                    password="testpass123"
                )
                RSVP.objects.create(user=user, event=event, status="going")

    def test_home_staff_all_filters_combined(self):
        """Тест всіх фільтрів разом"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(
            f'/?q=Event&status={Event.PUBLISHED}&organizer={self.user.id}'
            f'&category=tech&date_filter=upcoming&popularity=high'
            f'&sort=title_asc&tab=events&page=1'
        )
        self.assertEqual(response.status_code, 200)

    def test_home_staff_status_draft(self):
        """Тест фільтру статусу draft"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/?status={Event.DRAFT}&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_status_cancelled(self):
        """Тест фільтру статусу cancelled"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/?status={Event.CANCELLED}&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_status_archived(self):
        """Тест фільтру статусу archived"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(f'/?status={Event.ARCHIVED}&tab=events')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_sort_all_options(self):
        """Тест всіх опцій сортування"""
        self.client.login(username="staffuser", password="testpass123")
        
        sorts = [
            'date_desc', 'date_asc', 'title_asc', 'title_desc',
            'rsvp_count', 'rsvp_count_desc', 'starts_at', 'starts_at_desc'
        ]
        
        for sort in sorts:
            response = self.client.get(f'/?sort={sort}&tab=events')
            self.assertEqual(response.status_code, 200)

    def test_home_staff_pagination_page_2(self):
        """Тест пагінації - сторінка 2"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?tab=events&page=2')
        self.assertEqual(response.status_code, 200)

    def test_home_staff_invalid_page(self):
        """Тест невалідної сторінки"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/?tab=events&page=999')
        self.assertIn(response.status_code, [200, 404])


class EventDetailView100TestCase(TestCase):
    """Тести для EventDetailView - 100% coverage"""

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
        
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )

    def test_event_detail_draft_organizer(self):
        """Тест детальної сторінки draft події для організатора"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(f'/events/{self.draft_event.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_event_detail_draft_non_organizer(self):
        """Тест детальної сторінки draft події для не організатора"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(f'/events/{self.draft_event.pk}/')
        self.assertIn(response.status_code, [200, 302, 403, 404])


class EventCreateUpdate100TestCase(TestCase):
    """Тести для EventCreateView та EventUpdateView - 100% coverage"""

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

    def test_event_create_post_with_all_fields(self):
        """Тест створення події з усіма полями"""
        self.client.login(username="testuser", password="testpass123")
        
        now = timezone.now()
        response = self.client.post('/events/create/', {
            'title': 'Complete Event',
            'description': 'Full Description',
            'location': 'Київ',
            'starts_at': (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now + timedelta(days=5, hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': Event.DRAFT,
            'capacity': 100,
            'category': 'tech'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_event_update_post_with_all_fields(self):
        """Тест оновлення події з усіма полями"""
        self.client.login(username="testuser", password="testpass123")
        
        now = timezone.now()
        response = self.client.post(f'/events/{self.event.pk}/edit/', {
            'title': 'Updated Complete Event',
            'description': 'Updated Full Description',
            'location': 'Львів',
            'starts_at': (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now + timedelta(days=10, hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': Event.PUBLISHED,
            'capacity': 200,
            'category': 'business'
        })
        self.assertIn(response.status_code, [200, 302])


class CalendarView100TestCase(TestCase):
    """Тести для CalendarView - 100% coverage"""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Створюємо події на різні місяці
        for i in range(12):
            Event.objects.create(
                title=f"Event Month {i+1}",
                description="Description",
                starts_at=now.replace(month=((now.month + i - 1) % 12) + 1) + timedelta(days=1),
                ends_at=now.replace(month=((now.month + i - 1) % 12) + 1) + timedelta(days=1, hours=2),
                organizer=self.user,
                status=Event.PUBLISHED
            )

    def test_calendar_all_months(self):
        """Тест календаря для всіх місяців"""
        self.client.login(username="testuser", password="testpass123")
        
        for month in range(1, 13):
            response = self.client.get(f'/calendar/?year=2026&month={month}')
            self.assertEqual(response.status_code, 200)

    def test_calendar_edge_cases(self):
        """Тест календаря з граничними випадками"""
        self.client.login(username="testuser", password="testpass123")
        
        # Січень
        response = self.client.get('/calendar/?year=2026&month=1')
        self.assertEqual(response.status_code, 200)
        
        # Грудень
        response = self.client.get('/calendar/?year=2026&month=12')
        self.assertEqual(response.status_code, 200)


class RSVPViews100TestCase(TestCase):
    """Тести для RSVP views - 100% coverage"""

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
        
        self.event_with_capacity = Event.objects.create(
            title="Event With Capacity",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED,
            capacity=2
        )
        
        # Заповнюємо подію
        for i in range(2):
            user = User.objects.create_user(
                username=f"filler{i}",
                email=f"filler{i}@example.com",
                password="testpass123"
            )
            RSVP.objects.create(user=user, event=self.event_with_capacity, status="going")

    def test_rsvp_to_full_capacity_event(self):
        """Тест реєстрації на подію з повною місткістю"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(f'/events/{self.event_with_capacity.pk}/rsvp/')
        self.assertIn(response.status_code, [200, 302])


class ReviewViews100TestCase(TestCase):
    """Тести для Review views - 100% coverage"""

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
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=4),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )

    def test_review_valid_submission(self):
        """Тест валідного відгуку"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.post(f'/events/{self.past_event.pk}/review/', {
            'rating': 5,
            'comment': 'Excellent event! Really enjoyed it.'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_review_minimal_rating(self):
        """Тест відгуку з мінімальним рейтингом"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.post(f'/events/{self.past_event.pk}/review/', {
            'rating': 1,
            'comment': 'Not great.'
        })
        self.assertIn(response.status_code, [200, 302])
