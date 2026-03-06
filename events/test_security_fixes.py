"""
Тести для виправлень безпеки та архітектури
- Object-level permissions в API
- Валідація дат в serializers
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from events.models import Event
from events.serializers import EventSerializer
from events.views import IsOrganizerOrReadOnly


class IsOrganizerOrReadOnlyPermissionTestCase(TestCase):
    """Тести для object-level permission IsOrganizerOrReadOnly"""

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )

    def test_permission_allows_read_for_anyone(self):
        """Читання дозволено всім"""
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        
        factory = APIRequestFactory()
        permission = IsOrganizerOrReadOnly()
        
        # GET запит
        request = factory.get('/api/events/')
        request.user = self.other_user
        
        self.assertTrue(permission.has_object_permission(request, None, self.event))

    def test_permission_allows_write_for_organizer(self):
        """Запис дозволено організатору"""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        permission = IsOrganizerOrReadOnly()
        
        # PUT запит від організатора
        request = factory.put('/api/events/1/')
        request.user = self.organizer
        
        self.assertTrue(permission.has_object_permission(request, None, self.event))

    def test_permission_denies_write_for_non_organizer(self):
        """Запис заборонено не-організатору"""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        permission = IsOrganizerOrReadOnly()
        
        # PUT запит від іншого користувача
        request = factory.put('/api/events/1/')
        request.user = self.other_user
        
        self.assertFalse(permission.has_object_permission(request, None, self.event))


class EventAPIPermissionsTestCase(APITestCase):
    """Інтеграційні тести для API permissions"""

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizer",
            email="organizer@example.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        self.event = Event.objects.create(
            title="Test Event",
            description="Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.organizer,
            status=Event.DRAFT
        )
        
        self.client = APIClient()

    def test_organizer_can_update_own_event(self):
        """Організатор може оновити свою подію"""
        self.client.force_authenticate(user=self.organizer)
        
        response = self.client.patch(
            f'/api/events/{self.event.pk}/',
            {'title': 'Updated Title'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Title')

    def test_non_organizer_cannot_update_event(self):
        """Не-організатор не може оновити чужу подію"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.patch(
            f'/api/events/{self.event.pk}/',
            {'title': 'Hacked Title'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_organizer_cannot_delete_event(self):
        """Не-організатор не може видалити чужу подію"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.delete(f'/api/events/{self.event.pk}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_organizer_can_delete_own_event(self):
        """Організатор може видалити свою подію"""
        self.client.force_authenticate(user=self.organizer)
        
        response = self.client.delete(f'/api/events/{self.event.pk}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_anyone_can_read_event(self):
        """Будь-хто може читати події"""
        response = self.client.get(f'/api/events/{self.event.pk}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EventSerializerDateValidationTestCase(TestCase):
    """Тести для валідації дат в EventSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_starts_at_in_past_rejected_for_new_event(self):
        """Дата початку в минулому відхиляється для нової події"""
        now = timezone.now()
        
        serializer = EventSerializer(data={
            'title': 'Test Event',
            'description': 'Description',
            'starts_at': (now - timedelta(days=1)).isoformat(),
            'ends_at': (now + timedelta(hours=2)).isoformat(),
            'status': Event.DRAFT,
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('starts_at', serializer.errors)

    def test_starts_at_in_future_accepted(self):
        """Дата початку в майбутньому приймається"""
        now = timezone.now()
        
        serializer = EventSerializer(data={
            'title': 'Test Event',
            'description': 'Description',
            'starts_at': (now + timedelta(days=1)).isoformat(),
            'ends_at': (now + timedelta(days=1, hours=2)).isoformat(),
            'status': Event.DRAFT,
        })
        
        self.assertTrue(serializer.is_valid())

    def test_ends_at_before_starts_at_rejected(self):
        """Дата закінчення раніше початку відхиляється"""
        now = timezone.now()
        
        serializer = EventSerializer(data={
            'title': 'Test Event',
            'description': 'Description',
            'starts_at': (now + timedelta(days=2)).isoformat(),
            'ends_at': (now + timedelta(days=1)).isoformat(),
            'status': Event.DRAFT,
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('ends_at', serializer.errors)

    def test_ends_at_after_starts_at_accepted(self):
        """Дата закінчення пізніше початку приймається"""
        now = timezone.now()
        
        serializer = EventSerializer(data={
            'title': 'Test Event',
            'description': 'Description',
            'starts_at': (now + timedelta(days=1)).isoformat(),
            'ends_at': (now + timedelta(days=1, hours=2)).isoformat(),
            'status': Event.DRAFT,
        })
        
        self.assertTrue(serializer.is_valid())

    def test_update_existing_event_allows_past_starts_at(self):
        """Оновлення існуючої події дозволяє starts_at в минулому"""
        now = timezone.now()
        
        event = Event.objects.create(
            title="Old Event",
            description="Description",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=5, hours=-2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        serializer = EventSerializer(
            instance=event,
            data={'title': 'Updated Title'},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
