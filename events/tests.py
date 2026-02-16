from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.test import APITestCase
from rest_framework import status
import json

from .models import Event, Review
from .strategies import get_sort_strategy, STRATEGIES
from .specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    EventByLocationSpecification,
    apply_specifications,
)
from .decorators import organizer_required, event_not_archived
from tickets.models import RSVP
from notifications.models import Notification


User = get_user_model()


class EventReviewPermissionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.event = Event.objects.create(
            title="Test event",
            description="Desc",
            location="Loc",
            starts_at=timezone.now() - timezone.timedelta(days=2),
            ends_at=timezone.now() - timezone.timedelta(days=1),
            status=Event.ARCHIVED,
            organizer=self.user,
        )

    def test_cannot_review_without_rsvp(self):
        self.client.login(username="user", password="pass")
        url = reverse("event-review-create", kwargs={"pk": self.event.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)

    def test_can_review_with_rsvp_after_event(self):
        other_user = User.objects.create_user(username="participant", password="pass")
        RSVP.objects.create(user=other_user, event=self.event)

        self.client.login(username="participant", password="pass")
        url = reverse("event-review-create", kwargs={"pk": self.event.pk})
        resp = self.client.post(url, {"rating": "5", "comment": "Great"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Review.objects.filter(user=other_user, event=self.event).count(), 1)


class StrategyPatternTests(TestCase):
    """Тести для Strategy Pattern (сортування)"""
    
    def setUp(self):
        self.user = User.objects.create_user(username="organizer", password="pass")
        # Створюємо події з різними датами
        self.event1 = Event.objects.create(
            title="Alpha Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.user,
        )
        self.event2 = Event.objects.create(
            title="Beta Event",
            starts_at=timezone.now() + timezone.timedelta(days=2),
            ends_at=timezone.now() + timezone.timedelta(days=2, hours=2),
            status=Event.PUBLISHED,
            organizer=self.user,
        )
        self.event3 = Event.objects.create(
            title="Gamma Event",
            starts_at=timezone.now() + timezone.timedelta(days=3),
            ends_at=timezone.now() + timezone.timedelta(days=3, hours=2),
            status=Event.PUBLISHED,
            organizer=self.user,
        )
        # Додаємо RSVP для популярності
        user2 = User.objects.create_user(username="user2", password="pass")
        user3 = User.objects.create_user(username="user3", password="pass")
        RSVP.objects.create(user=user2, event=self.event2)
        RSVP.objects.create(user=user3, event=self.event2)
        RSVP.objects.create(user=user2, event=self.event1)

    def test_sort_by_popular_strategy_exists(self):
        """Перевіряє, що стратегія 'popular' існує"""
        self.assertIn("popular", STRATEGIES)
    
    def test_sort_by_popular_works(self):
        """Перевіряє, що sort=popular сортує по rsvp_count"""
        strategy = get_sort_strategy("popular")
        qs = Event.objects.annotate(
            rsvp_count=Count("rsvps", filter=Q(rsvps__status="going"), distinct=True)
        )
        sorted_qs = strategy.sort(qs)
        # event2 має 2 RSVP, event1 має 1 RSVP, event3 має 0 RSVP
        titles = list(sorted_qs.values_list("title", flat=True))
        self.assertEqual(titles[0], "Beta Event")  # 2 RSVP
        self.assertEqual(titles[1], "Alpha Event")  # 1 RSVP
    
    def test_sort_by_alphabet_works(self):
        """Перевіряє, що sort=alphabet сортує за абеткою"""
        strategy = get_sort_strategy("alphabet")
        qs = Event.objects.all()
        sorted_qs = strategy.sort(qs)
        titles = list(sorted_qs.values_list("title", flat=True))
        self.assertEqual(titles[0], "Alpha Event")
        self.assertEqual(titles[1], "Beta Event")
        self.assertEqual(titles[2], "Gamma Event")

    def test_unknown_strategy_returns_default(self):
        """Перевіряє, що невідомий slug повертає дефолтну стратегію"""
        strategy = get_sort_strategy("unknown_slug")
        self.assertEqual(strategy.slug, "date")


class SpecificationPatternTests(TestCase):
    """Тести для Specification Pattern (фільтрація)"""
    
    def setUp(self):
        self.user = User.objects.create_user(username="organizer", password="pass")
        self.event1 = Event.objects.create(
            title="Django Conference",
            location="Київ",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.user,
        )
        self.event2 = Event.objects.create(
            title="Python Meetup",
            location="Львів",
            starts_at=timezone.now() + timezone.timedelta(days=2),
            ends_at=timezone.now() + timezone.timedelta(days=2, hours=2),
            status=Event.DRAFT,
            organizer=self.user,
        )
    
    def test_status_specification(self):
        """Перевіряє фільтрацію за статусом"""
        spec = EventByStatusSpecification(Event.PUBLISHED)
        qs = apply_specifications(Event.objects.all(), spec)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, "Django Conference")
    
    def test_title_specification(self):
        """Перевіряє фільтрацію за назвою"""
        spec = EventByTitleSpecification("Django")
        qs = apply_specifications(Event.objects.all(), spec)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, "Django Conference")
    
    def test_location_specification(self):
        """Перевіряє фільтрацію за локацією"""
        spec = EventByLocationSpecification("Львів")
        qs = apply_specifications(Event.objects.all(), spec)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, "Python Meetup")
    
    def test_combined_specifications(self):
        """Перевіряє комбінування специфікацій"""
        spec1 = EventByStatusSpecification(Event.PUBLISHED)
        spec2 = EventByLocationSpecification("Київ")
        qs = apply_specifications(Event.objects.all(), spec1, spec2)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, "Django Conference")


class ObserverPatternTests(TestCase):
    """Тести для Observer Pattern (Django Signals)"""
    
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.participant = User.objects.create_user(username="participant", password="pass")
        self.event = Event.objects.create(
            title="Test Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )
        # Учасник реєструється
        RSVP.objects.create(user=self.participant, event=self.event)
    
    def test_cancel_event_creates_one_notification(self):
        """Перевіряє, що скасування події створює ОДНЕ сповіщення (не дублює)"""
        initial_count = Notification.objects.filter(
            notification_type=Notification.EVENT_CANCELLED
        ).count()
        
        # Скасовуємо подію
        self.event.status = Event.CANCELLED
        self.event.save()
        
        final_count = Notification.objects.filter(
            notification_type=Notification.EVENT_CANCELLED
        ).count()
        
        # Має бути рівно 1 нове сповіщення
        self.assertEqual(final_count - initial_count, 1)
    
    def test_rsvp_creates_notification_for_organizer(self):
        """Перевіряє, що RSVP створює сповіщення для організатора"""
        new_user = User.objects.create_user(username="newuser", password="pass")
        
        initial_count = Notification.objects.filter(
            user=self.organizer,
            notification_type=Notification.RSVP_CONFIRMED
        ).count()
        
        # Новий користувач реєструється
        RSVP.objects.create(user=new_user, event=self.event)
        
        final_count = Notification.objects.filter(
            user=self.organizer,
            notification_type=Notification.RSVP_CONFIRMED
        ).count()
        
        self.assertEqual(final_count - initial_count, 1)


class DecoratorPatternTests(TestCase):
    """Тести для Decorator Pattern (контроль доступу)"""
    
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.event = Event.objects.create(
            title="Test Event",
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=2),
            status=Event.PUBLISHED,
            organizer=self.organizer,
        )
        self.archived_event = Event.objects.create(
            title="Archived Event",
            starts_at=timezone.now() - timezone.timedelta(days=2),
            ends_at=timezone.now() - timezone.timedelta(days=1),
            status=Event.ARCHIVED,
            organizer=self.organizer,
        )
    
    def test_organizer_can_access_participants(self):
        """Перевіряє, що організатор має доступ до списку учасників"""
        self.client.login(username="organizer", password="pass")
        url = reverse("event-participants", kwargs={"pk": self.event.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
    
    def test_other_user_cannot_access_participants(self):
        """Перевіряє, що інший користувач не має доступу до списку учасників"""
        self.client.login(username="other", password="pass")
        url = reverse("event-participants", kwargs={"pk": self.event.pk})
        resp = self.client.get(url)
        # Має редіректити (302) з повідомленням про помилку
        self.assertEqual(resp.status_code, 302)
    
    def test_cannot_cancel_archived_event(self):
        """Перевіряє, що архівну подію не можна скасувати"""
        self.client.login(username="organizer", password="pass")
        url = reverse("event-cancel", kwargs={"pk": self.archived_event.pk})
        resp = self.client.post(url)
        # Має редіректити з повідомленням
        self.assertEqual(resp.status_code, 302)
        # Статус не змінився
        self.archived_event.refresh_from_db()
        self.assertEqual(self.archived_event.status, Event.ARCHIVED)


class APIRSVPTimeConflictTests(APITestCase):
    """API тести для перевірки конфлікту часу RSVP"""
    
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", 
            password="testpass"
        )
        self.other_user = get_user_model().objects.create_user(
            username="organizer", 
            password="testpass"
        )
        
        # Базова подія: завтра 10:00-12:00
        self.base_event = Event.objects.create(
            title="Base Event",
            starts_at=timezone.now() + timezone.timedelta(days=1, hours=10),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=12),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        
        # Подія з перетином: завтра 11:00-13:00
        self.overlapping_event = Event.objects.create(
            title="Overlapping Event",
            starts_at=timezone.now() + timezone.timedelta(days=1, hours=11),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=13),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        
        # Подія без перетину: завтра 14:00-16:00
        self.non_overlapping_event = Event.objects.create(
            title="Non-overlapping Event",
            starts_at=timezone.now() + timezone.timedelta(days=1, hours=14),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=16),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )

    def test_api_rsvp_success_when_no_conflict(self):
        """API RSVP успішний, якщо немає конфлікту часу"""
        self.client.force_authenticate(user=self.user)
        
        url = f"/api/events/{self.base_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RSVP.objects.filter(user=self.user, event=self.base_event).exists())

    def test_api_rsvp_fails_with_time_conflict(self):
        """API RSVP повертає 400, якщо є конфлікт часу"""
        # Спочатку реєструємося на base_event
        RSVP.objects.create(user=self.user, event=self.base_event)
        
        self.client.force_authenticate(user=self.user)
        
        # Намагаємося зареєструватися на overlapping_event
        url = f"/api/events/{self.overlapping_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Конфлікт часу", response.data["error"])
        self.assertIn("Base Event", response.data["error"])
        
        # RSVP не створено
        self.assertFalse(RSVP.objects.filter(user=self.user, event=self.overlapping_event).exists())

    def test_api_rsvp_success_when_no_time_overlap(self):
        """API RSVP успішний для подій без перетину часу"""
        # Реєструємося на base_event
        RSVP.objects.create(user=self.user, event=self.base_event)
        
        self.client.force_authenticate(user=self.user)
        
        # Намагаємося зареєструватися на non_overlapping_event
        url = f"/api/events/{self.non_overlapping_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RSVP.objects.filter(user=self.user, event=self.non_overlapping_event).exists())

    def test_api_rsvp_fails_when_already_registered(self):
        """API RSVP повертає 400, якщо вже зареєстрований"""
        # Спочатку реєструємося
        RSVP.objects.create(user=self.user, event=self.base_event)
        
        self.client.force_authenticate(user=self.user)
        
        # Намагаємося зареєструватися знову
        url = f"/api/events/{self.base_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("вже зареєстровані", response.data["error"])

    def test_api_rsvp_fails_when_capacity_full(self):
        """API RSVP повертає 400, якщо місця закінчились"""
        # Встановлюємо capacity = 1
        self.base_event.capacity = 1
        self.base_event.save()
        
        # Інший користувач займає єдине місце
        RSVP.objects.create(user=self.other_user, event=self.base_event)
        
        self.client.force_authenticate(user=self.user)
        
        url = f"/api/events/{self.base_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("місця зайняті", response.data["error"])

    def test_api_rsvp_requires_authentication(self):
        """API RSVP вимагає автентифікації"""
        url = f"/api/events/{self.base_event.id}/rsvp/"
        response = self.client.post(url)
        
        # DRF з permission_classes повертає 403, а не 401
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_rsvp_fails_for_draft_event(self):
        """API RSVP повертає 400 для draft події"""
        draft_event = Event.objects.create(
            title="Draft Event",
            starts_at=timezone.now() + timezone.timedelta(days=1, hours=10),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=12),
            status=Event.DRAFT,
            organizer=self.other_user,
        )
        
        self.client.force_authenticate(user=self.user)
        
        url = f"/api/events/{draft_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("не опублікована", response.data["error"])

    def test_api_rsvp_fails_for_cancelled_event(self):
        """API RSVP повертає 400 для скасованої події"""
        cancelled_event = Event.objects.create(
            title="Cancelled Event",
            starts_at=timezone.now() + timezone.timedelta(days=1, hours=10),
            ends_at=timezone.now() + timezone.timedelta(days=1, hours=12),
            status=Event.CANCELLED,
            organizer=self.other_user,
        )
        
        self.client.force_authenticate(user=self.user)
        
        url = f"/api/events/{cancelled_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("скасовано", response.data["error"])

    def test_api_rsvp_fails_for_archived_event(self):
        """API RSVP повертає 400 для архівованої події"""
        archived_event = Event.objects.create(
            title="Archived Event",
            starts_at=timezone.now() - timezone.timedelta(days=2),
            ends_at=timezone.now() - timezone.timedelta(days=1),
            status=Event.ARCHIVED,
            organizer=self.other_user,
        )
        
        self.client.force_authenticate(user=self.user)
        
        url = f"/api/events/{archived_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("архівована", response.data["error"])

    def test_api_rsvp_fails_for_started_event(self):
        """API RSVP повертає 400 для вже розпочатої події"""
        started_event = Event.objects.create(
            title="Started Event",
            starts_at=timezone.now() - timezone.timedelta(hours=1),
            ends_at=timezone.now() + timezone.timedelta(hours=1),
            status=Event.PUBLISHED,
            organizer=self.other_user,
        )
        
        self.client.force_authenticate(user=self.user)
        
        url = f"/api/events/{started_event.id}/rsvp/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("вже розпочалась", response.data["error"])
