"""
Декоратори для контролю доступу (Decorator Pattern)
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from .models import Event


def organizer_required(view_func):
    """
    Декоратор для перевірки, чи користувач є організатором події.
    
    Використання:
        @login_required
        @organizer_required
        def my_view(request, pk):
            ...
    """

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.organizer != request.user:
            messages.error(request, "Ви не маєте прав для виконання цієї дії")
            return redirect('event_detail', pk=pk)
        return view_func(request, pk, *args, **kwargs)

    return wrapper


def event_published_required(view_func):
    """
    Декоратор для перевірки, чи подія опублікована.
    Використовується для RSVP та інших публічних дій.
    """

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.status != Event.PUBLISHED:
            messages.warning(request, "Ця дія доступна тільки для опублікованих подій")
            return redirect('event_detail', pk=pk)
        return view_func(request, pk, *args, **kwargs)

    return wrapper


def event_not_archived(view_func):
    """
    Декоратор для заборони дій з архівними подіями.
    """

    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.status == Event.ARCHIVED:
            messages.warning(request, "Дія недоступна для архівних подій")
            return redirect('event_detail', pk=pk)
        return view_func(request, pk, *args, **kwargs)

    return wrapper
