from django.db import models
from django.contrib.auth import get_user_model


class Event(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

    STATUS_CHOICES = [
        (DRAFT, "draft"),
        (PUBLISHED, "published"),
        (CANCELLED, "cancelled"),
        (ARCHIVED, "archived"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Тип події (вільний текст, наприклад: конференція, вебінар, воркшоп)",
    )
    latitude = models.FloatField(null=True, blank=True, help_text="Широта місця проведення (наприклад, 50.4501)")
    longitude = models.FloatField(null=True, blank=True, help_text="Довгота місця проведення (наприклад, 30.5234)")
    organizer = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name="organized_events",
        help_text="Користувач, який створив подію"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="event_reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review({self.user_id} -> {self.event_id}, rating={self.rating})"

