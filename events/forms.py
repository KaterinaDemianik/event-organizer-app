from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    starts_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    ends_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "starts_at",
            "ends_at",
            "status",
        ]
