from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import UserProfile


class SignupForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        help_text="До 30 символів. Літери, цифри та @/./+/-/_",
        widget=forms.TextInput(attrs={"maxlength": "30", "placeholder": "username"}),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)


class AdminUserCreateForm(UserCreationForm):
    """Форма створення користувача для адміна"""
    email = forms.EmailField(
        required=False,
        label="Email (опціонально)",
        widget=forms.EmailInput(attrs={"placeholder": "user@example.com"})
    )
    is_staff = forms.BooleanField(
        required=False,
        label="Адміністратор",
        help_text="Чи має користувач права адміна?"
    )
    
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "password1", "password2", "is_staff")


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False,
        label="Ім'я",
        widget=forms.TextInput(attrs={"placeholder": "Ваше ім'я"}),
    )
    last_name = forms.CharField(
        required=False,
        label="Прізвище",
        widget=forms.TextInput(attrs={"placeholder": "Ваше прізвище"}),
    )
    email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "user@example.com"}),
    )

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")

    birth_date = forms.DateField(
        required=False,
        label="Дата народження",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    city = forms.CharField(
        required=False,
        label="Місто",
        widget=forms.TextInput(attrs={"placeholder": "Ваше місто"}),
    )
    phone = forms.CharField(
        required=False,
        label="Телефон",
        widget=forms.TextInput(attrs={"placeholder": "+380..."}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            profile = getattr(instance, "profile", None)
            if profile:
                self.fields["birth_date"].initial = profile.birth_date
                self.fields["city"].initial = profile.city
                self.fields["phone"].initial = profile.phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.birth_date = self.cleaned_data.get("birth_date")
        profile.city = self.cleaned_data.get("city", "")
        profile.phone = self.cleaned_data.get("phone", "")
        if commit:
            profile.save()
        return user
