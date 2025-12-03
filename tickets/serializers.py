from rest_framework import serializers
from .models import RSVP


class RSVPSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSVP
        fields = ["id", "user", "event", "status", "created_at"]
        read_only_fields = ["id", "user", "event", "created_at"]