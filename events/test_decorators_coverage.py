"""
Тести для decorators.py - Decorator Pattern для контролю доступу
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.decorators import (
    organizer_required,
    event_not_archived,
    event_not_cancelled,
    event_not_started
)


class DecoratorsTestCase(TestCase):
    """Тести для декораторів контролю доступу"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.factory = RequestFactory()
        
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
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )
        
        now = timezone.now()
        
        # Звичайна подія (організатор - testuser)
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Архівна подія
        self.archived_event = Event.objects.create(
            title="Archived Event",
            description="Archived Description",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.user,
            status=Event.ARCHIVED
        )
        
        # Скасована подія
        self.cancelled_event = Event.objects.create(
            title="Cancelled Event",
            description="Cancelled Description",
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=2),
            organizer=self.user,
            status=Event.CANCELLED
        )
        
        # Подія що вже розпочалась
        self.started_event = Event.objects.create(
            title="Started Event",
            description="Started Description",
            starts_at=now - timedelta(hours=1),  # Розпочалась годину тому
            ends_at=now + timedelta(hours=1),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def add_session_and_messages(self, request):
        """Додає сесію та повідомлення до request"""
        middleware = SessionMiddleware(lambda req: HttpResponse())
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

    def create_test_view(self):
        """Створює тестовий view для декораторів"""
        def test_view(request, pk):
            return HttpResponse("Success")
        return test_view

    def test_organizer_required_success_organizer(self):
        """Тест успішного доступу організатора"""
        @organizer_required
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
        # Перевіряємо що event додано до request
        self.assertEqual(request.event, self.event)

    def test_organizer_required_success_staff(self):
        """Тест успішного доступу staff користувача"""
        @organizer_required
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.staff_user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")

    def test_organizer_required_denied(self):
        """Тест відмови доступу для не-організатора"""
        @organizer_required
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.other_user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, f'/events/{self.event.pk}/')

    def test_organizer_required_nonexistent_event(self):
        """Тест для неіснуючої події"""
        @organizer_required
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get('/events/999/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        # Має викинути Http404
        with self.assertRaises(Exception):  # get_object_or_404 викидає Http404
            test_view(request, 999)

    def test_event_not_archived_success(self):
        """Тест успішного доступу до не-архівної події"""
        @event_not_archived
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")

    def test_event_not_archived_denied(self):
        """Тест відмови доступу до архівної події"""
        @event_not_archived
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.archived_event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.archived_event.pk)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, f'/events/{self.archived_event.pk}/')

    def test_event_not_archived_with_existing_event_in_request(self):
        """Тест використання існуючого event з request"""
        @event_not_archived
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        request.event = self.event  # Попередньо встановлений event
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)

    def test_event_not_cancelled_success(self):
        """Тест успішного доступу до не-скасованої події"""
        @event_not_cancelled
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")

    def test_event_not_cancelled_denied(self):
        """Тест відмови доступу до скасованої події"""
        @event_not_cancelled
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.cancelled_event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.cancelled_event.pk)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, f'/events/{self.cancelled_event.pk}/')

    def test_event_not_started_success(self):
        """Тест успішного доступу до події що ще не розпочалась"""
        @event_not_started
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")

    def test_event_not_started_denied(self):
        """Тест відмови доступу до події що вже розпочалась"""
        @event_not_started
        def test_view(request, pk):
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.started_event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.started_event.pk)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, f'/events/{self.started_event.pk}/')

    def test_decorator_chaining(self):
        """Тест ланцюжка декораторів"""
        @organizer_required
        @event_not_archived
        @event_not_cancelled
        def test_view(request, pk):
            return HttpResponse("Success")
        
        # Тест успішного проходження всіх декораторів
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")

    def test_decorator_chaining_failure_organizer(self):
        """Тест падіння на першому декораторі в ланцюжку"""
        @organizer_required
        @event_not_archived
        def test_view(request, pk):
            return HttpResponse("Success")
        
        # Не-організатор не пройде перший декоратор
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.other_user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        
        self.assertEqual(response.status_code, 302)  # Redirect від organizer_required

    def test_decorator_chaining_failure_archived(self):
        """Тест падіння на другому декораторі в ланцюжку"""
        @organizer_required
        @event_not_archived
        def test_view(request, pk):
            return HttpResponse("Success")
        
        # Організатор пройде перший декоратор, але не пройде другий (архівна подія)
        request = self.factory.get(f'/events/{self.archived_event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.archived_event.pk)
        
        self.assertEqual(response.status_code, 302)  # Redirect від event_not_archived

    def test_decorator_preserves_function_metadata(self):
        """Тест що декоратори зберігають метадані функції"""
        @organizer_required
        def test_view(request, pk):
            """Test view docstring"""
            return HttpResponse("Success")
        
        # Перевіряємо що @wraps зберіг метадані
        self.assertEqual(test_view.__name__, "test_view")
        self.assertEqual(test_view.__doc__, "Test view docstring")

    def test_event_assignment_in_decorators(self):
        """Тест що декоратори правильно встановлюють request.event"""
        @event_not_archived
        def test_view(request, pk):
            # Перевіряємо що event встановлений в request
            self.assertEqual(request.event, self.event)
            return HttpResponse("Success")
        
        request = self.factory.get(f'/events/{self.event.pk}/')
        request.user = self.user
        self.add_session_and_messages(request)
        
        response = test_view(request, self.event.pk)
        self.assertEqual(response.status_code, 200)
