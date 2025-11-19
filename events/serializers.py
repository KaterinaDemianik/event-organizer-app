from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    rsvp_count = serializers.IntegerField(read_only=True, help_text="Кількість підтверджень участі")
    
    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "location",
            "starts_at",
            "ends_at",
            "status",
            "organizer",
            "rsvp_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "organizer", "rsvp_count"]
