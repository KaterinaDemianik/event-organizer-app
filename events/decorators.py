"""
Декоратори для контролю доступу (Decorator Pattern)
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from .models import Event


def organizer_required(view_func):
    """
    Декоратор для перевірки, чи користувач є організатором події або staff.
    
    Використання:
        @login_required
        @organizer_required
        def my_view(request, pk):
            ...
    """

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.organizer != request.user and not request.user.is_staff:
            messages.error(request, "Ви не маєте прав для виконання цієї дії")
            return redirect('event_detail', pk=pk)
        request.event = event  # Передаємо event у request для повторного використання
        return view_func(request, pk, *args, **kwargs)

    return wrapper


def event_not_archived(view_func):
    """
    Декоратор для заборони дій з архівними подіями.
    Використовує event з request.event якщо доступний (від organizer_required).
    """

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = getattr(request, 'event', None) or get_object_or_404(Event, pk=pk)
        if event.status == Event.ARCHIVED:
            messages.warning(request, "Дія недоступна для архівних подій")
            return redirect('event_detail', pk=pk)
        request.event = event
        return view_func(request, pk, *args, **kwargs)

    return wrapper


def event_not_cancelled(view_func):
    """
    Декоратор для заборони дій зі скасованими подіями.
    """

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = getattr(request, 'event', None) or get_object_or_404(Event, pk=pk)
        if event.status == Event.CANCELLED:
            messages.warning(request, "Дія недоступна для скасованих подій")
            return redirect('event_detail', pk=pk)
        request.event = event
        return view_func(request, pk, *args, **kwargs)

    return wrapper


def event_not_started(view_func):
    """
    Декоратор для заборони дій з подіями, які вже розпочались.
    """
    from django.utils import timezone

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = getattr(request, 'event', None) or get_object_or_404(Event, pk=pk)
        if event.starts_at <= timezone.now():
            messages.warning(request, "Дія недоступна: подія вже розпочалась")
            return redirect('event_detail', pk=pk)
        request.event = event
        return view_func(request, pk, *args, **kwargs)

    return wrapper