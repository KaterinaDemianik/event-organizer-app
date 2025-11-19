from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


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
