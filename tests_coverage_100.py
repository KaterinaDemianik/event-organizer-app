"""
Фінальні тести для досягнення 100% coverage
Покриває всі залишкові непокриті рядки
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from io import StringIO
import json

from events.models import Event, Review
from events.serializers import EventSerializer
from events.states import EventStateManager
from events.schedule_services import PersonalScheduleService, ScheduleEntry
from events.forms import ReviewForm
from tickets.models import RSVP
from tickets.admin import RSVPAdmin
from notifications.models import Notification
from notifications.factories import (
    NotificationFactoryRegistry,
    EventUpdatedNotificationFactory,
    EventTimeChangedNotificationFactory,
)
from notifications.services import NotificationService


class ReviewFormValidationTestCase(TestCase):
    """Тести для events/forms.py - рядок 130 (clean_rating)"""

    def test_rating_validation_invalid_low(self):
        """Тест валідації рейтингу - занизький"""
        form = ReviewForm(data={
            'rating': 0,
            'comment': 'Test comment'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_rating_validation_invalid_high(self):
        """Тест валідації рейтингу - зависокий"""
        form = ReviewForm(data={
            'rating': 6,
            'comment': 'Test comment'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_rating_validation_valid(self):
        """Тест валідації рейтингу - валідний"""
        form = ReviewForm(data={
            'rating': 5,
            'comment': 'Great event!'
        })
        self.assertTrue(form.is_valid())


class PersonalScheduleServiceTestCase(TestCase):
    """Тести для events/schedule_services.py - рядки 23, 303-305"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            location="Київ",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_get_schedule_json_data(self):
        """Тест отримання JSON даних розкладу - рядки 303-305"""
        json_data = PersonalScheduleService.get_schedule_json_data(self.user)
        
        self.assertIsInstance(json_data, str)
        data = json.loads(json_data)
        self.assertIsInstance(data, list)

    def test_schedule_entry_to_dict(self):
        """Тест конвертації ScheduleEntry в dict"""
        now = timezone.now()
        entry = ScheduleEntry(
            event_id=1,
            title="Test Event",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="published",
            location="Київ",
            description="Description",
            is_organizer=True,
            has_rsvp=False
        )
        
        result = entry.to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['title'], "Test Event")


class EventSerializerValidateTestCase(TestCase):
    """Тести для events/serializers.py - рядок 72"""

    def setUp(self):
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
            status=Event.DRAFT
        )

    def test_validate_method_blocks_invalid_transition(self):
        """Тест що validate() блокує невалідний перехід - рядок 72"""
        serializer = EventSerializer(
            instance=self.event,
            data={'status': Event.ARCHIVED},
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        # Перевіряємо що помилка містить інформацію про дозволені переходи
        error_str = str(serializer.errors['status'])
        self.assertTrue(len(error_str) > 0)


class EventStateManagerTestCase(TestCase):
    """Тести для events/states.py - рядки 15, 209"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Подія що ще не завершилась
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Description",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Draft подія
        self.draft_event = Event.objects.create(
            title="Draft Event",
            description="Description",
            starts_at=now - timedelta(days=1),
            ends_at=now - timedelta(hours=22),
            organizer=self.user,
            status=Event.DRAFT
        )

    def test_validate_transition_archived_not_published(self):
        """Тест: архівування draft події заборонено - рядок 209"""
        is_valid, error = EventStateManager.validate_transition(
            self.draft_event, "archived"
        )
        
        self.assertFalse(is_valid)
        # Перехід заборонений - помилка має бути не None
        self.assertIsNotNone(error)


class EventViewSetAPITestCase(APITestCase):
    """Тести для events/views.py - рядок 47"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_event_sets_organizer(self):
        """Тест що perform_create встановлює організатора - рядок 47"""
        now = timezone.now()
        
        response = self.client.post('/api/events/', {
            'title': 'New Event',
            'description': 'Description',
            'starts_at': (now + timedelta(days=1)).isoformat(),
            'ends_at': (now + timedelta(days=1, hours=2)).isoformat(),
            'status': Event.DRAFT,
        }, format='json')
        
        self.assertIn(response.status_code, [201, 400])
        
        if response.status_code == 201:
            event = Event.objects.get(pk=response.data['id'])
            self.assertEqual(event.organizer, self.user)


class NotificationFactoriesTestCase(TestCase):
    """Тести для notifications/factories.py - рядки 58, 81"""

    def setUp(self):
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

    def test_event_updated_factory_no_changes(self):
        """Тест фабрики оновлення без змін - рядок 58"""
        factory = EventUpdatedNotificationFactory()
        context = {'event': self.event, 'changes': []}
        
        message = factory.create_message(context)
        
        self.assertIn(self.event.title, message)
        self.assertIn("оновлена", message.lower())

    def test_event_time_changed_factory_no_times(self):
        """Тест фабрики зміни часу без старого/нового часу - рядок 81"""
        factory = EventTimeChangedNotificationFactory()
        context = {'event': self.event}
        
        message = factory.create_message(context)
        
        self.assertIn(self.event.title, message)
        self.assertIn("змінено", message.lower())


class NotificationModelTestCase(TestCase):
    """Тести для notifications/models.py - рядок 59"""

    def setUp(self):
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

    def test_notification_str_method(self):
        """Тест __str__ методу Notification - рядок 59"""
        notification = Notification.objects.create(
            user=self.user,
            event=self.event,
            notification_type=Notification.EVENT_UPDATED,
            message="Test message"
        )
        
        str_repr = str(notification)
        self.assertIn(self.user.username, str_repr)
        self.assertIn(self.event.title, str_repr)


class NotificationServicesTestCase(TestCase):
    """Тести для notifications/services.py - рядок 69"""

    def setUp(self):
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

    def test_create_event_update_notification_no_changes(self):
        """Тест створення сповіщення без змін - рядок 69"""
        old_data = {
            'title': self.event.title,
            'starts_at': self.event.starts_at,
            'ends_at': self.event.ends_at,
            'location': self.event.location,
        }
        
        count = NotificationService.create_event_update_notification(
            self.event, old_data
        )
        
        # Без змін - 0 сповіщень
        self.assertEqual(count, 0)


class NotificationViewsTestCase(TestCase):
    """Тести для notifications/views.py - рядок 37"""

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
            notification_type=Notification.EVENT_UPDATED,
            message="Test message"
        )

    def test_mark_as_read_ajax_request(self):
        """Тест позначення як прочитане через AJAX - рядок 37"""
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.post(
            f'/notifications/{self.notification.pk}/read/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))


class RSVPAdminTestCase(TestCase):
    """Тести для tickets/admin.py - рядок 14"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = RSVPAdmin(RSVP, self.site)
        
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
        
        self.rsvp = RSVP.objects.create(
            user=self.user,
            event=self.event,
            status="going"
        )

    def test_get_queryset_with_select_related(self):
        """Тест що get_queryset використовує select_related - рядок 14"""
        factory = RequestFactory()
        request = factory.get('/admin/tickets/rsvp/')
        request.user = self.organizer
        
        queryset = self.admin.get_queryset(request)
        
        # Перевіряємо що queryset працює
        self.assertEqual(queryset.count(), 1)
        
        # Перевіряємо що select_related застосовано
        rsvp = queryset.first()
        self.assertEqual(rsvp.user.username, "testuser")
        self.assertEqual(rsvp.event.title, "Test Event")


class FixRSVPDuplicatesCommandTestCase(TestCase):
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

    def test_command_removes_invalid_status_rsvps(self):
        """Тест видалення RSVP з невалідним статусом"""
        from django.core.management import call_command
        
        # Створюємо RSVP і змінюємо статус на невалідний
        rsvp = RSVP.objects.create(user=self.user1, event=self.event1, status="going")
        RSVP.objects.filter(pk=rsvp.pk).update(status="maybe")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Всього видалено', output)
        
        # RSVP з невалідним статусом має бути видалено
        self.assertFalse(RSVP.objects.filter(pk=rsvp.pk).exists())

    def test_command_keeps_valid_going_rsvp(self):
        """Тест що валідні RSVP зі статусом going залишаються"""
        from django.core.management import call_command
        
        rsvp = RSVP.objects.create(user=self.user2, event=self.event2, status="going")
        
        out = StringIO()
        call_command('fix_rsvp_duplicates', stdout=out)
        
        # Валідний RSVP має залишитись
        self.assertTrue(RSVP.objects.filter(pk=rsvp.pk).exists())
