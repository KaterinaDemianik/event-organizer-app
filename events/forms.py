from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Event, Review

User = get_user_model()


class EventForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Дата початку"
    )
    ends_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Дата закінчення"
    )
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "latitude",
            "longitude",
            "starts_at",
            "ends_at",
            "status",
            "category",
            "capacity",
        ]
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Локалізуємо назви деяких полів форми
        if "capacity" in self.fields:
            self.fields["capacity"].label = "Максимальна кількість учасників"
        if "status" in self.fields:
            self.fields["status"].label = "Статус події"
        if "category" in self.fields:
            self.fields["category"].label = "Категорія події"

        # Якщо користувач - адмін, показуємо поле organizer
        if user and user.is_staff:
            self.fields['organizer'] = forms.ModelChoiceField(
                queryset=User.objects.all(),
                label="Організатор",
                initial=user,
                required=True
            )
            self.Meta.fields.insert(0, 'organizer')
    
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
        capacity = cleaned_data.get('capacity')
        
        if starts_at and ends_at:
            if ends_at <= starts_at:
                raise forms.ValidationError(
                    "Дата закінчення має бути пізніше дати початку події."
                )

        # Перевірка місткості
        if capacity is not None:
            if capacity <= 0:
                self.add_error("capacity", "Місткість має бути додатним числом або порожньою (без обмежень).")
        
        return cleaned_data


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(1, 6)],
        widget=forms.Select(),
        label="Рейтинг (1-5)",
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_rating(self):
        value = int(self.cleaned_data["rating"])
        if value < 1 or value > 5:
            raise forms.ValidationError("Рейтинг має бути від 1 до 5.")
        return value
