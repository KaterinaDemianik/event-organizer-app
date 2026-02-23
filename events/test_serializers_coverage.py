"""
Тести для serializers.py - покриття EventSerializer
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase

from events.models import Event
from events.serializers import EventSerializer
from tickets.models import RSVP


class EventSerializerTestCase(APITestCase):
    """Тести для EventSerializer"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            location="Test Location",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_event_serializer_fields(self):
        """Тест що серіалізер містить всі необхідні поля"""
        # Анотуємо подію з rsvp_count
        from django.db.models import Count, Q
        annotated_event = Event.objects.annotate(
            rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True)
        ).get(pk=self.event.pk)
        
        serializer = EventSerializer(instance=annotated_event)
        data = serializer.data
        
        expected_fields = [
            "id", "title", "description", "location", 
            "starts_at", "ends_at", "status", "organizer",
            "rsvp_count", "created_at", "updated_at"
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)

    def test_event_serializer_data_content(self):
        """Тест правильності даних серіалізера"""
        serializer = EventSerializer(instance=self.event)
        data = serializer.data
        
        self.assertEqual(data['title'], "Test Event")
        self.assertEqual(data['description'], "Test Description")
        self.assertEqual(data['location'], "Test Location")
        self.assertEqual(data['status'], Event.PUBLISHED)
        self.assertEqual(data['organizer'], self.user.id)

    def test_event_serializer_rsvp_count(self):
        """Тест підрахунку RSVP в серіалізері"""
        # Створюємо кілька RSVP
        RSVP.objects.create(user=self.user, event=self.event, status="going")
        
        # Створюємо другого користувача та його RSVP
        user2 = User.objects.create_user(username="user2", password="pass")
        RSVP.objects.create(user=user2, event=self.event, status="going")
        
        # Анотуємо подію з підрахунком RSVP
        from django.db.models import Count, Q
        annotated_event = Event.objects.annotate(
            rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True)
        ).get(pk=self.event.pk)
        
        serializer = EventSerializer(instance=annotated_event)
        data = serializer.data
        
        self.assertEqual(data['rsvp_count'], 2)

    def test_event_serializer_read_only_fields(self):
        """Тест що read_only поля не можна змінити через серіалізер"""
        initial_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'id': 999,  # Спроба змінити read_only поле
            'organizer': 999,  # Спроба змінити read_only поле
            'rsvp_count': 999,  # Спроба змінити read_only поле
        }
        
        serializer = EventSerializer(instance=self.event, data=initial_data, partial=True)
        
        if serializer.is_valid():
            updated_event = serializer.save()
            
            # Перевіряємо що тільки не-readonly поля оновились
            self.assertEqual(updated_event.title, 'Updated Title')
            self.assertEqual(updated_event.description, 'Updated Description')
            
            # Read-only поля не мають змінитись
            self.assertEqual(updated_event.id, self.event.id)
            self.assertEqual(updated_event.organizer, self.user)

    def test_event_serializer_validation(self):
        """Тест валідації серіалізера"""
        # Тест з валідними даними
        valid_data = {
            'title': 'New Event',
            'description': 'New Description',
            'location': 'New Location',
            'starts_at': timezone.now() + timedelta(days=1),
            'ends_at': timezone.now() + timedelta(days=1, hours=2),
            'status': Event.DRAFT
        }
        
        serializer = EventSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_event_serializer_invalid_data(self):
        """Тест серіалізера з невалідними даними"""
        # Тест без обов'язкових полів
        invalid_data = {
            'description': 'Description without title'
        }
        
        serializer = EventSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_event_serializer_create(self):
        """Тест створення події через серіалізер"""
        data = {
            'title': 'Serializer Event',
            'description': 'Created via serializer',
            'location': 'Serializer Location',
            'starts_at': timezone.now() + timedelta(days=2),
            'ends_at': timezone.now() + timedelta(days=2, hours=2),
            'status': Event.DRAFT
        }
        
        serializer = EventSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Встановлюємо організатора вручну (оскільки це read_only поле)
        event = serializer.save(organizer=self.user)
        
        self.assertEqual(event.title, 'Serializer Event')
        self.assertEqual(event.organizer, self.user)

    def test_event_serializer_update(self):
        """Тест оновлення події через серіалізер"""
        update_data = {
            'title': 'Updated via Serializer',
            'location': 'Updated Location'
        }
        
        serializer = EventSerializer(instance=self.event, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_event = serializer.save()
        
        self.assertEqual(updated_event.title, 'Updated via Serializer')
        self.assertEqual(updated_event.location, 'Updated Location')
        # Інші поля не мають змінитись
        self.assertEqual(updated_event.description, 'Test Description')

    def test_event_serializer_help_text(self):
        """Тест що rsvp_count має правильний help_text"""
        serializer = EventSerializer()
        rsvp_count_field = serializer.fields['rsvp_count']
        
        self.assertEqual(rsvp_count_field.help_text, "Кількість підтверджень участі")
        self.assertTrue(rsvp_count_field.read_only)

    def test_event_serializer_meta_configuration(self):
        """Тест конфігурації Meta класу"""
        serializer = EventSerializer()
        
        # Перевіряємо що модель правильно встановлена
        self.assertEqual(serializer.Meta.model, Event)
        
        # Перевіряємо що всі поля присутні
        expected_fields = [
            "id", "title", "description", "location",
            "starts_at", "ends_at", "status", "organizer",
            "rsvp_count", "created_at", "updated_at"
        ]
        self.assertEqual(serializer.Meta.fields, expected_fields)
        
        # Перевіряємо read_only поля
        expected_readonly = ["id", "created_at", "updated_at", "organizer", "rsvp_count"]
        self.assertEqual(serializer.Meta.read_only_fields, expected_readonly)
