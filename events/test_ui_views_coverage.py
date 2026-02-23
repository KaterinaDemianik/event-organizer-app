"""
Тести для ui_views.py - покриття основних view функцій та класів
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from unittest.mock import patch, MagicMock
import json

from events.models import Event, Review
from tickets.models import RSVP
from events.services import RSVPService


class UIViewsTestCase(TestCase):
    """Базовий клас для тестів UI views"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.client = Client()
        
        # Користувачі
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
        
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Події
        self.published_event = Event.objects.create(
            title="Published Event",
            description="Published Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED,
            location="Test Location"
        )
        
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Draft Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )
        
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Past Description",
            starts_at=now - timedelta(days=2),
            ends_at=now - timedelta(days=2, hours=2),
            organizer=self.organizer,
            status=Event.PUBLISHED
        )


class HomeViewTestCase(UIViewsTestCase):
    """Тести для home_view"""

    def test_home_view_anonymous_user(self):
        """Тест головної сторінки для анонімного користувача"""
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Анонімний користувач має бачити список подій
        self.assertContains(response, "Published Event")

    def test_home_view_regular_user(self):
        """Тест головної сторінки для звичайного користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_home_view_staff_user_default(self):
        """Тест головної сторінки для staff користувача (адмін панель)"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        # Staff користувач має бачити адмін панель
        self.assertContains(response, "events_count")

    def test_home_view_staff_user_with_period_filter(self):
        """Тест адмін панелі з фільтром періоду"""
        self.client.login(username="staffuser", password="testpass123")
        
        # Тест з періодом "today"
        response = self.client.get('/?period=today')
        self.assertEqual(response.status_code, 200)
        
        # Тест з періодом "week"
        response = self.client.get('/?period=week')
        self.assertEqual(response.status_code, 200)
        
        # Тест з періодом "month"
        response = self.client.get('/?period=month')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_user_custom_period(self):
        """Тест адмін панелі з кастомним періодом"""
        self.client.login(username="staffuser", password="testpass123")
        
        today = date.today()
        date_from = today.strftime('%Y-%m-%d')
        date_to = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = self.client.get(f'/?period=custom&date_from={date_from}&date_to={date_to}')
        self.assertEqual(response.status_code, 200)

    def test_home_view_staff_user_invalid_custom_period(self):
        """Тест адмін панелі з невалідним кастомним періодом"""
        self.client.login(username="staffuser", password="testpass123")
        
        # Невалідна дата
        response = self.client.get('/?period=custom&date_from=invalid-date')
        self.assertEqual(response.status_code, 200)
        # Має використати дефолтний період


class EventListViewTestCase(UIViewsTestCase):
    """Тести для EventListView"""

    def test_event_list_view_basic(self):
        """Тест базового списку подій"""
        response = self.client.get(reverse('event_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")
        self.assertNotContains(response, "Draft Event")  # Чернетки не показуються

    def test_event_list_view_with_search(self):
        """Тест списку подій з пошуком"""
        response = self.client.get(reverse('event_list') + '?q=Published')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_event_list_view_with_status_filter(self):
        """Тест списку подій з фільтром статусу"""
        response = self.client.get(reverse('event_list') + f'?status={Event.PUBLISHED}')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_event_list_view_with_location_filter(self):
        """Тест списку подій з фільтром локації"""
        response = self.client.get(reverse('event_list') + '?location=Test')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_event_list_view_with_category_filter(self):
        """Тест списку подій з фільтром категорії"""
        # Встановлюємо категорію для події
        self.published_event.category = "tech"
        self.published_event.save()
        
        response = self.client.get(reverse('event_list') + '?category=tech')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_event_list_view_with_sorting(self):
        """Тест списку подій з сортуванням"""
        # Тест сортування за датою
        response = self.client.get(reverse('event_list') + '?sort=date')
        self.assertEqual(response.status_code, 200)
        
        # Тест сортування за популярністю
        response = self.client.get(reverse('event_list') + '?sort=popular')
        self.assertEqual(response.status_code, 200)
        
        # Тест сортування за абеткою
        response = self.client.get(reverse('event_list') + '?sort=alphabet')
        self.assertEqual(response.status_code, 200)

    def test_event_list_view_pagination(self):
        """Тест пагінації списку подій"""
        # Створюємо багато подій для тестування пагінації
        for i in range(25):
            Event.objects.create(
                title=f"Event {i}",
                description=f"Description {i}",
                starts_at=timezone.now() + timedelta(days=i+10),
                ends_at=timezone.now() + timedelta(days=i+10, hours=2),
                organizer=self.organizer,
                status=Event.PUBLISHED
            )
        
        # Перша сторінка
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
        
        # Друга сторінка
        response = self.client.get(reverse('event_list') + '?page=2')
        self.assertEqual(response.status_code, 200)


class EventDetailViewTestCase(UIViewsTestCase):
    """Тести для EventDetailView"""

    def test_event_detail_view_anonymous(self):
        """Тест детальної сторінки події для анонімного користувача"""
        response = self.client.get(reverse('event_detail', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")
        self.assertContains(response, "Published Description")

    def test_event_detail_view_authenticated(self):
        """Тест детальної сторінки події для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event_detail', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_event_detail_view_organizer(self):
        """Тест детальної сторінки події для організатора"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(reverse('event_detail', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")
        # Організатор має бачити додаткові дії

    def test_event_detail_view_with_rsvp(self):
        """Тест детальної сторінки події з RSVP"""
        # Створюємо RSVP
        RSVP.objects.create(
            user=self.user,
            event=self.published_event,
            status="going"
        )
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event_detail', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)

    def test_event_detail_view_nonexistent(self):
        """Тест детальної сторінки неіснуючої події"""
        response = self.client.get(reverse('event_detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class EventCreateViewTestCase(UIViewsTestCase):
    """Тести для EventCreateView"""

    def test_event_create_view_anonymous(self):
        """Тест створення події анонімним користувачем"""
        response = self.client.get(reverse('event-create'))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    def test_event_create_view_authenticated_get(self):
        """Тест GET запиту на створення події"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event-create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_event_create_view_authenticated_post_valid(self):
        """Тест POST запиту на створення події з валідними даними"""
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
        
        response = self.client.post(reverse('event-create'), data=form_data)
        
        # Має перенаправити після успішного створення
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо що подія створена
        self.assertTrue(Event.objects.filter(title='New Event').exists())

    def test_event_create_view_authenticated_post_invalid(self):
        """Тест POST запиту на створення події з невалідними даними"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'title': '',  # Пуста назва
            'description': 'New Description',
        }
        
        response = self.client.post(reverse('event-create'), data=form_data)
        
        # Має повернути форму з помилками
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")


class EventUpdateViewTestCase(UIViewsTestCase):
    """Тести для EventUpdateView"""

    def test_event_update_view_anonymous(self):
        """Тест редагування події анонімним користувачем"""
        response = self.client.get(reverse('event_edit', kwargs={'pk': self.published_event.pk}))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    def test_event_update_view_not_organizer(self):
        """Тест редагування події не організатором"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event_edit', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити з повідомленням про помилку
        self.assertEqual(response.status_code, 302)

    def test_event_update_view_organizer_get(self):
        """Тест GET запиту на редагування події організатором"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(reverse('event_edit', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Event")

    def test_event_update_view_organizer_post_valid(self):
        """Тест POST запиту на редагування події з валідними даними"""
        self.client.login(username="organizer", password="testpass123")
        
        now = timezone.now()
        form_data = {
            'title': 'Updated Event',
            'description': 'Updated Description',
            'location': 'Updated Location',
            'starts_at': (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': (now + timedelta(days=1, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': Event.PUBLISHED,
            'capacity': 100
        }
        
        response = self.client.post(
            reverse('event-edit', kwargs={'pk': self.published_event.pk}), 
            data=form_data
        )
        
        # Має перенаправити після успішного оновлення
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо що подія оновлена
        updated_event = Event.objects.get(pk=self.published_event.pk)
        self.assertEqual(updated_event.title, 'Updated Event')

    def test_event_update_view_staff_user(self):
        """Тест редагування події staff користувачем"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(reverse('event_edit', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)


class RSVPViewsTestCase(UIViewsTestCase):
    """Тести для RSVP view функцій"""

    def test_rsvp_view_anonymous(self):
        """Тест реєстрації на подію анонімним користувачем"""
        response = self.client.post(reverse('rsvp', kwargs={'pk': self.published_event.pk}))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    @patch.object(RSVPService, 'can_create_rsvp')
    def test_rsvp_view_authenticated_success(self, mock_can_create):
        """Тест успішної реєстрації на подію"""
        mock_can_create.return_value = (True, None)
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse('rsvp', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити з повідомленням про успіх
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо що RSVP створено
        self.assertTrue(RSVP.objects.filter(user=self.user, event=self.published_event).exists())

    @patch.object(RSVPService, 'can_create_rsvp')
    def test_rsvp_view_authenticated_failure(self, mock_can_create):
        """Тест неуспішної реєстрації на подію"""
        mock_can_create.return_value = (False, "Test error message")
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse('rsvp', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити з повідомленням про помилку
        self.assertEqual(response.status_code, 302)

    def test_rsvp_cancel_view_anonymous(self):
        """Тест скасування реєстрації анонімним користувачем"""
        response = self.client.post(reverse('rsvp_cancel', kwargs={'pk': self.published_event.pk}))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    def test_rsvp_cancel_view_authenticated(self):
        """Тест скасування реєстрації авторизованим користувачем"""
        # Створюємо RSVP
        rsvp = RSVP.objects.create(
            user=self.user,
            event=self.published_event,
            status="going"
        )
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse('rsvp_cancel', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо що RSVP видалено
        self.assertFalse(RSVP.objects.filter(pk=rsvp.pk).exists())


class EventActionViewsTestCase(UIViewsTestCase):
    """Тести для дій з подіями (скасування, архівування)"""

    def test_event_cancel_view_anonymous(self):
        """Тест скасування події анонімним користувачем"""
        response = self.client.post(reverse('event_cancel', kwargs={'pk': self.published_event.pk}))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    def test_event_cancel_view_not_organizer(self):
        """Тест скасування події не організатором"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse('event_cancel', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити з повідомленням про помилку
        self.assertEqual(response.status_code, 302)

    def test_event_cancel_view_organizer(self):
        """Тест скасування події організатором"""
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(reverse('event_cancel', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо що подія скасована
        updated_event = Event.objects.get(pk=self.published_event.pk)
        self.assertEqual(updated_event.status, Event.CANCELLED)

    def test_event_archive_view_organizer(self):
        """Тест архівування події організатором"""
        # Робимо подію завершеною
        past_time = timezone.now() - timedelta(hours=1)
        self.published_event.ends_at = past_time
        self.published_event.save()
        
        self.client.login(username="organizer", password="testpass123")
        response = self.client.post(reverse('event-archive', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити
        self.assertEqual(response.status_code, 302)

    def test_event_participants_view_organizer(self):
        """Тест перегляду учасників події організатором"""
        # Створюємо кілька RSVP
        RSVP.objects.create(user=self.user, event=self.published_event, status="going")
        
        self.client.login(username="organizer", password="testpass123")
        response = self.client.get(reverse('event-participants', kwargs={'pk': self.published_event.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")


class EventReviewViewTestCase(UIViewsTestCase):
    """Тести для створення відгуків"""

    def test_event_review_create_anonymous(self):
        """Тест створення відгуку анонімним користувачем"""
        response = self.client.get(reverse('event_review_create', kwargs={'pk': self.past_event.pk}))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    def test_event_review_create_future_event(self):
        """Тест створення відгуку для майбутньої події"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event-review-create', kwargs={'pk': self.published_event.pk}))
        
        # Має перенаправити з повідомленням про помилку
        self.assertEqual(response.status_code, 302)

    def test_event_review_create_past_event_get(self):
        """Тест GET запиту на створення відгуку для завершеної події"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event_review_create', kwargs={'pk': self.past_event.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_event_review_create_past_event_post_valid(self):
        """Тест POST запиту на створення відгуку з валідними даними"""
        self.client.login(username="testuser", password="testpass123")
        
        form_data = {
            'rating': 5,
            'comment': 'Great event!'
        }
        
        response = self.client.post(
            reverse('event-review-create', kwargs={'pk': self.past_event.pk}), 
            data=form_data
        )
        
        # Має перенаправити після успішного створення
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо що відгук створено
        self.assertTrue(Review.objects.filter(event=self.past_event, user=self.user).exists())

    def test_event_review_create_duplicate(self):
        """Тест створення дублікату відгуку"""
        # Створюємо перший відгук
        Review.objects.create(
            event=self.past_event,
            user=self.user,
            rating=4,
            comment="First review"
        )
        
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('event_review_create', kwargs={'pk': self.past_event.pk}))
        
        # Має перенаправити з повідомленням про існуючий відгук
        self.assertEqual(response.status_code, 302)


class CalendarViewTestCase(UIViewsTestCase):
    """Тести для CalendarView"""

    def test_calendar_view_anonymous(self):
        """Тест календаря для анонімного користувача"""
        response = self.client.get(reverse('calendar'))
        # Має перенаправити на логін
        self.assertEqual(response.status_code, 302)

    def test_calendar_view_authenticated(self):
        """Тест календаря для авторизованого користувача"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('calendar'))
        
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_with_date_params(self):
        """Тест календаря з параметрами дати"""
        self.client.login(username="testuser", password="testpass123")
        
        # Тест з конкретним роком та місяцем
        response = self.client.get(reverse('calendar') + '?year=2024&month=12')
        self.assertEqual(response.status_code, 200)
        
        # Тест з невалідними параметрами
        response = self.client.get(reverse('calendar') + '?year=invalid&month=invalid')
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_json_response(self):
        """Тест JSON відповіді календаря"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('calendar'),
            HTTP_ACCEPT='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Перевіряємо що відповідь є валідним JSON
        data = json.loads(response.content)
        self.assertIn('entries', data)
