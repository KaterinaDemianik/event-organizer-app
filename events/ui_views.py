from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import timedelta, date
import json

from .models import Event, Review
from .forms import EventForm, ReviewForm
from .services import EventArchiveService
from .states import EventStateManager
from .schedule_services import PersonalScheduleService
from .specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    EventByLocationSpecification,
    apply_specifications,
)
from .decorators import (
    organizer_required,
    event_not_archived,
    event_not_cancelled,
    event_not_started,
)  # Всі декоратори реально використовуються в цьому файлі
from tickets.models import RSVP
from django.contrib.auth import get_user_model

User = get_user_model()

from .strategies import get_sort_strategy


def home_view(request):
    """Головна сторінка - адмін панель для staff, список подій для користувачів"""
    
    if request.user.is_authenticated and request.user.is_staff:
        from django.utils import timezone
        
        now = timezone.now()
        today = now.date()
        
        period = request.GET.get('period', 'all')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        if period == 'custom' and date_from:
            from datetime import datetime
            try:
                start_date = timezone.make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
                if date_to:
                    end_date = timezone.make_aware(datetime.strptime(date_to, '%Y-%m-%d'))
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    period_label = f"з {date_from} по {date_to}"
                else:
                    end_date = now
                    period_label = f"з {date_from}"
            except ValueError:
                start_date = None
                end_date = None
                period_label = "за весь час"
        elif period == 'today':
            start_date = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
            end_date = now
            period_label = "сьогодні"
        elif period == 'week':
            start_date = now - timedelta(days=7)
            end_date = now
            period_label = "за тиждень"
        elif period == 'month':
            start_date = now - timedelta(days=30)
            end_date = now
            period_label = "за місяць"
        elif period == 'quarter':
            start_date = now - timedelta(days=90)
            end_date = now
            period_label = "за квартал"
        elif period == 'year':
            start_date = now - timedelta(days=365)
            end_date = now
            period_label = "за рік"
        else:  # 'all'
            start_date = None
            end_date = None
            period_label = "за весь час"
        
        if start_date:
            events_qs = Event.objects.filter(created_at__gte=start_date)
            users_qs = User.objects.filter(date_joined__gte=start_date)
            rsvps_qs = RSVP.objects.filter(created_at__gte=start_date)
            
            if end_date:
                events_qs = events_qs.filter(created_at__lte=end_date)
                users_qs = users_qs.filter(date_joined__lte=end_date)
                rsvps_qs = rsvps_qs.filter(created_at__lte=end_date)
        else:
            events_qs = Event.objects.all()
            users_qs = User.objects.all()
            rsvps_qs = RSVP.objects.all()
        
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        stats = {
            'total_events': events_qs.count(),
            'published_events': events_qs.filter(status=Event.PUBLISHED).count(),
            'upcoming_events': events_qs.filter(starts_at__gte=now, status=Event.PUBLISHED).count(),
            'archived_events': events_qs.filter(status=Event.ARCHIVED).count(),
            
            'total_users': users_qs.count(),
            'new_users_week': users_qs.filter(date_joined__gte=week_ago).count(),
            'new_users_month': users_qs.filter(date_joined__gte=month_ago).count(),
            
            'total_rsvps': rsvps_qs.count(),
            'rsvps_week': rsvps_qs.filter(created_at__gte=week_ago).count(),
            'rsvps_month': rsvps_qs.filter(created_at__gte=month_ago).count(),
            
            'period_label': period_label,
        }
        
        tab = request.GET.get('tab', 'stats')
        
        q = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        organizer_filter = request.GET.get('organizer', '')
        category_filter = request.GET.get('category', '')
        date_filter = request.GET.get('date_filter', '')
        popularity_filter = request.GET.get('popularity', '')
        sort_by = request.GET.get('sort', 'date_desc')
        
        events_qs = Event.objects.annotate(rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True))
        if tab == 'events':
            if q:
                events_qs = events_qs.filter(
                    Q(title__icontains=q) | 
                    Q(description__icontains=q) | 
                    Q(location__icontains=q)
                )
            if status_filter:
                events_qs = events_qs.filter(status=status_filter)
            if organizer_filter:
                events_qs = events_qs.filter(organizer_id=organizer_filter)

            if category_filter:
                events_qs = events_qs.filter(category__icontains=category_filter)
            
            if date_filter:
                today = timezone.now().date()
                
                if date_filter == 'upcoming':
                    events_qs = events_qs.filter(starts_at__gte=timezone.now())
                elif date_filter == 'today':
                    events_qs = events_qs.filter(
                        starts_at__date=today
                    )
                elif date_filter == 'past':
                    events_qs = events_qs.filter(ends_at__lt=timezone.now())
                elif date_filter == 'this_week':
                    week_start = today - timedelta(days=today.weekday())
                    week_end = week_start + timedelta(days=7)
                    events_qs = events_qs.filter(
                        starts_at__date__gte=week_start,
                        starts_at__date__lt=week_end
                    )
                elif date_filter == 'this_month':
                    events_qs = events_qs.filter(
                        starts_at__year=today.year,
                        starts_at__month=today.month
                    )
            
            if popularity_filter:
                if popularity_filter == 'popular':
                    events_qs = events_qs.filter(rsvp_count__gte=5)
                elif popularity_filter == 'medium':
                    events_qs = events_qs.filter(rsvp_count__gte=1, rsvp_count__lt=5)
                elif popularity_filter == 'none':
                    events_qs = events_qs.filter(rsvp_count=0)
            
            if sort_by == 'date_desc':
                events_qs = events_qs.order_by('-created_at')
            elif sort_by == 'date_asc':
                events_qs = events_qs.order_by('created_at')
            elif sort_by == 'popular':
                events_qs = events_qs.order_by('-rsvp_count', '-created_at')
            elif sort_by == 'alphabet':
                events_qs = events_qs.order_by('title')
            elif sort_by == 'event_date':
                events_qs = events_qs.order_by('starts_at')
        
        events_count = events_qs.count()
        recent_events = events_qs[:100]
        
        if (tab == 'stats' or not tab) and start_date:
            top_events_qs = Event.objects.filter(created_at__gte=start_date)
            if end_date:
                top_events_qs = top_events_qs.filter(created_at__lte=end_date)
            top_events = top_events_qs.annotate(rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True)).order_by('-rsvp_count')[:5]
        else:
            top_events = Event.objects.annotate(rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True)).order_by('-rsvp_count')[:5]
        
        recent_users = User.objects.order_by('-date_joined')[:50]
        recent_rsvps = RSVP.objects.select_related('user', 'event').order_by('-created_at')[:50]
        all_users = User.objects.all().order_by('username')
        
        category_options = (
            Event.objects.exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )

        context = {
            'tab': tab,
            'stats': stats,
            'period': period,
            'date_from': date_from,
            'date_to': date_to,
            'top_events': top_events,
            'recent_events': recent_events,
            'events_count': events_count,
            'recent_users': recent_users,
            'recent_rsvps': recent_rsvps,
            'all_users': all_users,
            'q': q,
            'status': status_filter,
            'organizer': organizer_filter,
            'category': category_filter,
            'date_filter': date_filter,
            'popularity': popularity_filter,
            'sort': sort_by,
            'category_choices': category_options,
        }
        
        return render(request, 'admin_home.html', context)
    else:
        return redirect('event_list')


class EventListView(ListView):
    model = Event
    template_name = "events/list.html"
    context_object_name = "events"
    paginate_by = 10

    def get_queryset(self):
        EventArchiveService().archive_past_events()

        from django.db.models import Case, When, Value, IntegerField
        from django.db.models.functions import Greatest, Cast
        
        qs = (
            Event.objects
            .annotate(rsvp_count=Count("rsvps", filter=Q(rsvps__status="going"), distinct=True))
            .annotate(
                remaining_places=Case(
                    When(capacity__isnull=True, then=Value(None)),
                    default=Greatest(
                        Cast(F("capacity"), IntegerField()) - Cast(F("rsvp_count"), IntegerField()),
                        Value(0)
                    ),
                    output_field=IntegerField()
                )
            )
            .order_by("-starts_at")
        )
        
        view = self.request.GET.get("view", "all")
        
        if view == "my" and self.request.user.is_authenticated:
            qs = qs.filter(
                organizer=self.request.user
            ).exclude(status=Event.ARCHIVED)
        elif view == "upcoming" and self.request.user.is_authenticated:
            now = timezone.now()
            qs = qs.filter(
                starts_at__gte=now,
                status=Event.PUBLISHED,
                rsvps__user=self.request.user
            ).distinct()
        elif view == "archived" and self.request.user.is_authenticated:
            if self.request.user.is_staff:
                qs = qs.filter(status=Event.ARCHIVED)
            else:
                qs = qs.filter(status=Event.ARCHIVED).filter(
                    Q(organizer=self.request.user) | Q(rsvps__user=self.request.user)
                ).distinct()
        elif view == "all":
            qs = qs.filter(status=Event.PUBLISHED)
        
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

        category = self.request.GET.get("category")
        if category:
            filtered_qs = filtered_qs.filter(category__icontains=category)
        
        date_filter = self.request.GET.get("date_filter")
        if date_filter:
            today = timezone.now().date()
            
            if date_filter == 'upcoming':
                filtered_qs = filtered_qs.filter(starts_at__gte=timezone.now())
            elif date_filter == 'today':
                filtered_qs = filtered_qs.filter(starts_at__date=today)
            elif date_filter == 'this_week':
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=7)
                filtered_qs = filtered_qs.filter(
                    starts_at__date__gte=week_start,
                    starts_at__date__lt=week_end
                )
            elif date_filter == 'this_month':
                filtered_qs = filtered_qs.filter(
                    starts_at__year=today.year,
                    starts_at__month=today.month
                )
        
        popularity = self.request.GET.get("popularity")
        if popularity:
            if popularity == 'popular':
                filtered_qs = filtered_qs.filter(rsvp_count__gte=5)
            elif popularity == 'medium':
                filtered_qs = filtered_qs.filter(rsvp_count__gte=1, rsvp_count__lt=5)
            elif popularity == 'none':
                filtered_qs = filtered_qs.filter(rsvp_count=0)

        availability = self.request.GET.get("availability")
        if availability == "available":
            filtered_qs = filtered_qs.filter(
                Q(capacity__isnull=True) | Q(capacity__gt=F("rsvp_count"))
            )
        elif availability == "full":
            filtered_qs = filtered_qs.filter(
                capacity__isnull=False,
                capacity__lte=F("rsvp_count"),
            )

        sort_slug = self.request.GET.get("sort", "date")
        
        # Централізоване сортування через Strategy Pattern
        strategy = get_sort_strategy(sort_slug)
        self._current_sort = strategy.slug
        return strategy.sort(filtered_qs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        ctx["location"] = self.request.GET.get("location", "")
        ctx["view"] = self.request.GET.get("view", "all")
        ctx["date_filter"] = self.request.GET.get("date_filter", "")
        ctx["popularity"] = self.request.GET.get("popularity", "")
        ctx["availability"] = self.request.GET.get("availability", "")
        ctx["sort"] = getattr(self, "_current_sort", self.request.GET.get("sort", "date"))
        ctx["category"] = self.request.GET.get("category", "")

        ctx["category_choices"] = (
            Event.objects.exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )
        ctx["status_choices"] = [
            (Event.DRAFT, "Чернетка"),
            (Event.PUBLISHED, "Опубліковано"),
            (Event.CANCELLED, "Скасовано"),
            (Event.ARCHIVED, "Архів"),
        ]

        popular_tags_qs = (
            Event.objects.filter(status=Event.PUBLISHED)
            .exclude(category="")
            .values("category")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        ctx["popular_tags"] = [
            {"slug": row["category"], "label": row["category"], "count": row["count"]}
            for row in popular_tags_qs
        ]
        return ctx


class EventDetailView(DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"
    
    def get_object(self, queryset=None):
        """Перевіряє доступ до draft-подій"""
        event = super().get_object(queryset)
        
        # Draft події можуть бачити тільки їх організатори
        if event.status == Event.DRAFT:
            if not self.request.user.is_authenticated or event.organizer != self.request.user:
                from django.http import Http404
                raise Http404("Подія не знайдена")
        
        return event
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        event = self.object

        if self.request.user.is_authenticated:
            user_rsvp = RSVP.objects.filter(event=event, user=self.request.user).first()
            ctx["user_rsvp"] = user_rsvp
        else:
            user_rsvp = None
            ctx["user_rsvp"] = None

        ctx["rsvp_count"] = RSVP.objects.filter(event=event, status="going").count()

        if event.capacity is not None:
            remaining = event.capacity - ctx["rsvp_count"]
            ctx["remaining_places"] = remaining if remaining > 0 else 0
        else:
            ctx["remaining_places"] = None

        ctx["event_started"] = event.starts_at <= timezone.now()

        from django.db.models import Avg, Count

        reviews_qs = event.reviews.select_related("user")
        agg = reviews_qs.aggregate(avg_rating=Avg("rating"), reviews_count=Count("id"))
        ctx["reviews"] = reviews_qs
        ctx["avg_rating"] = agg["avg_rating"]
        ctx["reviews_count"] = agg["reviews_count"]

        can_review = False
        if self.request.user.is_authenticated:
            event_ended = event.ends_at <= timezone.now()
            has_rsvp = RSVP.objects.filter(event=event, user=self.request.user).exists()
            has_review = Review.objects.filter(event=event, user=self.request.user).exists()
            can_review = event_ended and has_rsvp and not has_review

        ctx["can_review"] = can_review
        
        from urllib.parse import urlencode
        from datetime import timezone as dt_timezone
        
        start_utc = event.starts_at.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        end_utc = event.ends_at.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        
        google_params = {
            'action': 'TEMPLATE',
            'text': event.title,
            'dates': f'{start_utc}/{end_utc}',
            'details': event.description or '',
            'location': event.location or '',
        }
        
        ctx["google_calendar_url"] = f"https://calendar.google.com/calendar/render?{urlencode(google_params)}"
        
        return ctx


@login_required
def event_review_create_view(request, pk: int):
    event = get_object_or_404(Event, pk=pk)

    if event.ends_at > timezone.now():
        messages.error(request, "Ви можете залишити відгук лише після завершення події.")
        return redirect("event_detail", pk=pk)

    if not RSVP.objects.filter(event=event, user=request.user).exists():
        messages.error(request, "Ви можете залишити відгук лише як учасник цієї події.")
        return redirect("event_detail", pk=pk)

    if Review.objects.filter(event=event, user=request.user).exists():
        messages.info(request, "Ви вже залишили відгук для цієї події.")
        return redirect("event_detail", pk=pk)

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.event = event
            review.user = request.user
            review.save()
            messages.success(request, "Дякуємо за ваш відгук!")
            return redirect("event_detail", pk=pk)
    else:
        form = ReviewForm()

    return render(request, "events/review_form.html", {"event": event, "form": form})


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
        if event.organizer != request.user and not request.user.is_staff:
            messages.error(request, "Ви не можете редагувати цю подію")
            return redirect("event_detail", pk=event.pk)
        
        if not EventStateManager.can_edit(event):
            messages.error(request, "Цю подію не можна редагувати в поточному стані")
            return redirect("event_detail", pk=event.pk)
        
        # Зберегти попередні значення для порівняння
        self.old_event_data = {
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'starts_at': event.starts_at,
            'ends_at': event.ends_at,
        }
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, "Подію оновлено успішно")
        
        # Створити сповіщення для учасників про зміни
        from notifications.services import NotificationService
        notifications_count = NotificationService.create_event_update_notification(
            self.object,
            self.old_event_data
        )
        
        if notifications_count > 0:
            messages.info(self.request, f"Сповіщення надіслано {notifications_count} учасникам")
        
        return resp


@login_required
@event_not_archived
@event_not_cancelled
@event_not_started
def rsvp_view(request, pk: int):
    """Реєстрація на подію (RSVP)"""
    from .services import RSVPService
    
    event = request.event  # Отримуємо з декоратора

    can_create, error_message = RSVPService.can_create_rsvp(request.user, event)
    if not can_create:
        messages.warning(request, error_message)
        return redirect("event_detail", pk=pk)

    RSVP.objects.create(user=request.user, event=event)
    messages.success(request, "Ваш RSVP збережено")
    return redirect("event_detail", pk=pk)


@login_required
@event_not_archived
def rsvp_cancel_view(request, pk: int):
    """Скасування реєстрації на подію"""
    if request.method == "POST":
        event = request.event  # Отримуємо з декоратора

        deleted_count, _ = RSVP.objects.filter(user=request.user, event=event).delete()
        if deleted_count > 0:
            messages.success(request, "Реєстрацію скасовано")
        else:
            messages.warning(request, "Ви не були зареєстровані на цю подію")
    return redirect("event_detail", pk=pk)


@login_required
@organizer_required
@event_not_archived
def event_cancel_view(request, pk: int):
    """Скасування події організатором або адміном"""
    if request.method == "POST":
        event = request.event  # Отримуємо з декоратора
        
        if not EventStateManager.can_cancel(event):
            messages.error(request, "Цю подію не можна скасувати в поточному стані")
            return redirect("event_detail", pk=pk)
        
        event.status = Event.CANCELLED
        event.save()
        # Сповіщення створюються автоматично через Django Signal (events/signals.py)
        
        messages.success(request, f"Подію '{event.title}' скасовано. Учасники отримають сповіщення.")
        
        return redirect("event_detail", pk=pk)
    
    return redirect("event_detail", pk=pk)


@login_required
@organizer_required
@event_not_archived
def event_archive_view(request, pk: int):
    """Архівування події організатором або адміном"""
    if request.method == "POST":
        event = request.event  # Отримуємо з декоратора
        
        # Використовуємо archive_event() з EventArchiveService
        archive_service = EventArchiveService()
        success, error_message = archive_service.archive_event(event)
        
        if success:
            messages.success(request, f"Подію '{event.title}' архівовано.")
        else:
            messages.error(request, f"Помилка архівування: {error_message}")
        
        return redirect("event_detail", pk=pk)
    
    return redirect("event_detail", pk=pk)


@login_required
@organizer_required
def event_participants_view(request, pk: int):
    """Список учасників події"""
    event = request.event  # Отримуємо з декоратора
    
    participants = RSVP.objects.filter(event=event).select_related('user').order_by('-created_at')
    
    context = {
        'event': event,
        'participants': participants,
    }
    
    return render(request, 'events/participants.html', context)


class CalendarView(ListView):
    """
    Календар подій з місячним та тижневим виглядом
    
    Підтримує GET-параметри для фільтрації та підсвічування:
    - schedule_filter: all|upcoming|organized|published
    - highlight: none|soon|organizer|popular
    """
    model = Event
    template_name = "events/calendar.html"
    context_object_name = "events"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return PersonalScheduleService.get_user_events_queryset(self.request.user)
        else:
            return Event.objects.filter(status=Event.PUBLISHED).order_by("starts_at")

    def _build_schedule_provider(self):
        """
        Побудувати ланцюжок декораторів на основі GET-параметрів
        
        Decorator Pattern: обгортки для фільтрації та підсвічування
        """
        from .schedule_services import (
            BaseScheduleProvider,
            FilteredScheduleDecorator,
            HighlightedScheduleDecorator,
        )
        
        schedule_filter = self.request.GET.get("schedule_filter", "all")
        highlight = self.request.GET.get("highlight", "none")
        
        provider = BaseScheduleProvider()
        
        if schedule_filter == "upcoming":
            provider = FilteredScheduleDecorator(provider, only_upcoming=True)
        elif schedule_filter == "organized":
            provider = FilteredScheduleDecorator(provider, only_organizer=True)
        elif schedule_filter == "published":
            provider = FilteredScheduleDecorator(provider, only_published=True)
        
        if highlight and highlight != "none":
            provider = HighlightedScheduleDecorator(provider, highlight_mode=highlight)
        
        return provider

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        schedule_filter = self.request.GET.get("schedule_filter", "all")
        highlight = self.request.GET.get("highlight", "none")
        
        context["schedule_filter"] = schedule_filter
        context["highlight"] = highlight
        
        if self.request.user.is_authenticated:
            provider = self._build_schedule_provider()
            entries = provider.get_entries(self.request.user)
            events_data = [entry.to_dict() for entry in entries]
            context['events_json'] = json.dumps(events_data)
        else:
            events_data = []
            for event in self.get_queryset():
                events_data.append({
                    'id': event.id,
                    'title': event.title,
                    'starts_at': event.starts_at.isoformat(),
                    'ends_at': event.ends_at.isoformat(),
                    'status': event.status,
                    'location': event.location or '',
                    'description': event.description or '',
                })
            context['events_json'] = json.dumps(events_data)
        
        return context