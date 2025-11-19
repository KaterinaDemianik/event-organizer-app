from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from datetime import timedelta

from .models import Event
from .forms import EventForm
from .specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    EventByLocationSpecification,
    apply_specifications,
)
from tickets.models import RSVP
from django.contrib.auth import get_user_model

User = get_user_model()

from .strategies import get_sort_strategy, get_sort_choices


def home_view(request):
    """Головна сторінка - адмін панель для staff, список подій для користувачів"""
    
    if request.user.is_authenticated and request.user.is_staff:
        # Адмін бачить статистику
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        stats = {
            'total_events': Event.objects.count(),
            'published_events': Event.objects.filter(status=Event.PUBLISHED).count(),
            'upcoming_events': Event.objects.filter(starts_at__gte=now, status=Event.PUBLISHED).count(),
            'archived_events': Event.objects.filter(status=Event.ARCHIVED).count(),
            
            'total_users': User.objects.count(),
            'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
            'new_users_month': User.objects.filter(date_joined__gte=month_ago).count(),
            
            'total_rsvps': RSVP.objects.count(),
            'rsvps_week': RSVP.objects.filter(created_at__gte=week_ago).count(),
            'rsvps_month': RSVP.objects.filter(created_at__gte=month_ago).count(),
        }
        
        tab = request.GET.get('tab', 'stats')
        
        top_events = Event.objects.annotate(rsvp_count=Count('rsvps')).order_by('-rsvp_count')[:5]
        recent_events = Event.objects.annotate(rsvp_count=Count('rsvps')).order_by('-created_at')[:50]
        recent_users = User.objects.order_by('-date_joined')[:50]
        recent_rsvps = RSVP.objects.select_related('user', 'event').order_by('-created_at')[:50]
        
        context = {
            'tab': tab,
            'stats': stats,
            'top_events': top_events,
            'recent_events': recent_events,
            'recent_users': recent_users,
            'recent_rsvps': recent_rsvps,
        }
        
        return render(request, 'admin_home.html', context)
    else:
        # Звичайні користувачі бачать список подій
        return redirect('event_list')


class EventListView(ListView):
    model = Event
    template_name = "events/list.html"
    context_object_name = "events"
    paginate_by = 10

    def get_queryset(self):
        # Додаємо анотацію з кількістю RSVP
        qs = Event.objects.annotate(rsvp_count=Count('rsvps')).order_by("-starts_at")
        
        # Фільтрація по вкладках
        view = self.request.GET.get("view", "all")
        
        if view == "my" and self.request.user.is_authenticated:
            # Мої події - де я організатор
            qs = qs.filter(organizer=self.request.user)
        elif view == "upcoming" and self.request.user.is_authenticated:
            # Заплановані - майбутні опубліковані події
            now = timezone.now()
            qs = qs.filter(
                starts_at__gte=now,
                status=Event.PUBLISHED
            )
        elif view == "archived" and self.request.user.is_authenticated:
            # Архів - завершені події
            qs = qs.filter(status=Event.ARCHIVED)
        # view == "all" - всі опубліковані події
        elif view == "all":
            qs = qs.filter(status=Event.PUBLISHED)
        
        # Збираємо специфікації на основі параметрів запиту
        specs = []
        
        q = self.request.GET.get("q")
        if q:
            specs.append(EventByTitleSpecification(q))
        
        status = self.request.GET.get("status")
        if status:
            specs.append(EventByStatusSpecification(status))
        
        location = self.request.GET.get("location")
        if location:
            specs.append(EventByLocationSpecification(location))
        
        filtered_qs = apply_specifications(qs, *specs)

        # Застосовуємо стратегію сортування
        sort_slug = self.request.GET.get("sort", "date")
        strategy = get_sort_strategy(sort_slug)
        self._current_sort = strategy.slug
        return strategy.sort(filtered_qs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["location"] = self.request.GET.get("location", "")
        ctx["view"] = self.request.GET.get("view", "all")
        ctx["sort"] = getattr(self, "_current_sort", self.request.GET.get("sort", "date"))
        ctx["sort_choices"] = get_sort_choices()
        ctx["status_choices"] = [
            (Event.DRAFT, "Чернетка"),
            (Event.PUBLISHED, "Опубліковано"),
            (Event.CANCELLED, "Скасовано"),
            (Event.ARCHIVED, "Архів"),
        ]
        return ctx


class EventDetailView(DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            from tickets.models import RSVP
            ctx["user_rsvp"] = RSVP.objects.filter(
                event=self.object, 
                user=self.request.user
            ).first()
        else:
            ctx["user_rsvp"] = None
        return ctx


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/create.html"
    success_url = reverse_lazy("home")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Для адміна organizer вже встановлено з форми
        # Для звичайних користувачів ставимо автоматично
        if not self.request.user.is_staff:
            form.instance.organizer = self.request.user
        resp = super().form_valid(form)
        messages.success(self.request, "Подію створено успішно")
        return resp


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/edit.html"
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy("event_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        # Перевіряємо, чи користувач є організатором або адміном
        if event.organizer != request.user and not request.user.is_staff:
            messages.error(request, "Ви не можете редагувати цю подію")
            return redirect("event_detail", pk=event.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Подію оновлено успішно")
        return resp


@login_required
def rsvp_view(request, pk: int):
    event = get_object_or_404(Event, pk=pk)
    _, created = RSVP.objects.get_or_create(user=request.user, event=event)
    if created:
        messages.success(request, "Ваш RSVP збережено")
    else:
        messages.info(request, "Ви вже підтвердили участь у цій події")
    return redirect("event_detail", pk=pk)


@login_required
def rsvp_cancel_view(request, pk: int):
    if request.method == "POST":
        event = get_object_or_404(Event, pk=pk)
        deleted_count, _ = RSVP.objects.filter(user=request.user, event=event).delete()
        if deleted_count > 0:
            messages.success(request, "Реєстрацію скасовано")
        else:
            messages.warning(request, "Ви не були зареєстровані на цю подію")
    return redirect("event_detail", pk=pk)


@login_required
def event_cancel_view(request, pk: int):
    """Скасування події організатором або адміном"""
    if request.method == "POST":
        event = get_object_or_404(Event, pk=pk)
        
        # Перевіряємо, чи користувач є організатором або адміном
        if event.organizer != request.user and not request.user.is_staff:
            messages.error(request, "Ви не можете скасувати цю подію")
            return redirect("event_detail", pk=pk)
        
        # Змінюємо статус на "cancelled"
        event.status = Event.CANCELLED
        event.save()
        
        messages.success(request, f"Подію '{event.title}' скасовано")
        return redirect("event_detail", pk=pk)
    
    return redirect("event_detail", pk=pk)
