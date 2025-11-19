from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from .forms import SignupForm, AdminUserCreateForm
from tickets.models import RSVP
from events.models import Event


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


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["user_obj"] = user
        ctx["rsvp_count"] = RSVP.objects.filter(user=user).count()
        ctx["my_events_count"] = Event.objects.filter(organizer=user).count()
        ctx["recent_rsvps"] = RSVP.objects.filter(user=user).select_related("event").order_by("-created_at")[:5]
        ctx["recent_events"] = Event.objects.filter(organizer=user).order_by("-created_at")[:5]
        return ctx


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
