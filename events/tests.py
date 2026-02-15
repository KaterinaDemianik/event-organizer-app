from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

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
