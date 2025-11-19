from django.db import models
from django.contrib.auth import get_user_model


class RSVP(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="rsvps")
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="rsvps")
    status = models.CharField(max_length=20, default="going")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "event")

    def __str__(self):
        return f"RSVP({self.user_id} -> {self.event_id})"

# Create your models here.
