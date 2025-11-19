from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from .models import Event
from .forms import EventForm
from .specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    EventByLocationSpecification,
    apply_specifications,
)
from tickets.models import RSVP


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
        
        # Застосовуємо всі специфікації
        return apply_specifications(qs, *specs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["location"] = self.request.GET.get("location", "")
        ctx["view"] = self.request.GET.get("view", "all")
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

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        resp = super().form_valid(form)
        messages.success(self.request, "Подію створено успішно")
        return resp


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/edit.html"
    
    def get_success_url(self):
        return reverse_lazy("event_detail", kwargs={"pk": self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        # Перевіряємо, чи користувач є організатором
        if event.organizer != request.user:
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
    """Скасування події організатором"""
    if request.method == "POST":
        event = get_object_or_404(Event, pk=pk)
        
        # Перевіряємо, чи користувач є організатором
        if event.organizer != request.user:
            messages.error(request, "Ви не можете скасувати цю подію")
            return redirect("event_detail", pk=pk)
        
        # Змінюємо статус на "cancelled"
        event.status = Event.CANCELLED
        event.save()
        
        messages.success(request, f"Подію '{event.title}' скасовано")
        return redirect("event_detail", pk=pk)
    
    return redirect("event_detail", pk=pk)
