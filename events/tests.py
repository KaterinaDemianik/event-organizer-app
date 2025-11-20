from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Event, Review
from tickets.models import RSVP


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

