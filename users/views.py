from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    PasswordChangeView,
    PasswordChangeDoneView,
)
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.db.models import Avg, Count
from django.utils import timezone
from django.contrib import messages
from .forms import SignupForm, AdminUserCreateForm, UserProfileForm
from tickets.models import RSVP
from events.models import Event, Review


class LoginView(DjangoLoginView):
    """Кастомний LoginView, який перенаправляє вже авторизованих користувачів"""
    template_name = "registration/login.html"
    
    def dispatch(self, request, *args, **kwargs):
        # Якщо користувач вже авторизований, перенаправляємо на головну
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class SignupView(FormView):
    template_name = "registration/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("home")
    
    def dispatch(self, request, *args, **kwargs):
        # Якщо користувач вже авторизований, перенаправляємо на головну
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "users/profile.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["user_obj"] = user
        base_rsvps = RSVP.objects.filter(user=user)
        ctx["rsvp_count"] = base_rsvps.count()

        # Події користувача як організатора
        my_events = Event.objects.filter(organizer=user)
        ctx["my_events_count"] = my_events.count()
        ctx["my_published_events_count"] = my_events.filter(status=Event.PUBLISHED).count()
        ctx["my_archived_events_count"] = my_events.filter(status=Event.ARCHIVED).count()

        # RSVP користувача: майбутні / минулі
        now = timezone.now()
        ctx["upcoming_rsvps_count"] = base_rsvps.filter(event__ends_at__gte=now).count()
        ctx["past_rsvps_count"] = base_rsvps.filter(event__ends_at__lt=now).count()

        ctx["recent_rsvps"] = base_rsvps.select_related("event").order_by("-created_at")[:5]
        ctx["recent_events"] = my_events.order_by("-created_at")[:5]

        # Відгуки про події користувача (як організатора)
        my_events_reviews = Review.objects.filter(event__organizer=user)
        agg = my_events_reviews.aggregate(
            avg_rating=Avg("rating"),
            reviews_count=Count("id"),
        )
        ctx["my_events_avg_rating"] = agg["avg_rating"]
        ctx["my_events_reviews_count"] = agg["reviews_count"]

        # Відгуки, які залишив користувач
        ctx["my_reviews_count"] = Review.objects.filter(user=user).count()

        # Вік користувача за датою народження (якщо вказана)
        profile = getattr(user, "profile", None)
        age = None
        if profile and profile.birth_date:
            today = timezone.now().date()
            bd = profile.birth_date
            age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        ctx["age"] = age
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Особисту інформацію оновлено")
        return super().form_valid(form)


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        messages.success(self.request, "Пароль успішно змінено.")
        return super().form_valid(form)


class UserPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"


@staff_member_required
def admin_create_user(request):
    """Створення користувача адміном"""
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Користувача {user.username} успішно створено!')
            return redirect('/?tab=users')
    else:
        form = AdminUserCreateForm()
    
    return render(request, 'users/admin_create_user.html', {'form': form})
