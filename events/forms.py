from django import forms
from django.utils import timezone
from .models import Event


class EventForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Дата початку"
    )
    ends_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Дата закінчення"
    )

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
    
    def clean_starts_at(self):
        starts_at = self.cleaned_data.get('starts_at')
        if starts_at and starts_at < timezone.now():
            raise forms.ValidationError(
                "Дата початку події не може бути в минулому. Оберіть майбутню дату."
            )
        return starts_at
    
    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get('starts_at')
        ends_at = cleaned_data.get('ends_at')
        
        if starts_at and ends_at:
            if ends_at <= starts_at:
                raise forms.ValidationError(
                    "Дата закінчення має бути пізніше дати початку події."
                )
        
        return cleaned_data
