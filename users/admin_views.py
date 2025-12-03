from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from tickets.models import RSVP
from django.contrib.auth import get_user_model

User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    """Кастомна адмін панель з статистикою"""
    
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
    
    top_events = Event.objects.annotate(
        rsvp_count=Count('rsvps')
    ).order_by('-rsvp_count')[:5]
    
    recent_events = Event.objects.order_by('-created_at')[:5]
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    recent_rsvps = RSVP.objects.select_related('user', 'event').order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'top_events': top_events,
        'recent_events': recent_events,
        'recent_users': recent_users,
        'recent_rsvps': recent_rsvps,
    }
    
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def admin_events_list(request):
    """Список всіх подій для адміна"""
    events = Event.objects.annotate(
        rsvp_count=Count('rsvps')
    ).select_related('organizer').order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        events = events.filter(status=status)
    
    context = {
        'events': events,
        'status_filter': status,
        'status_choices': Event.STATUS_CHOICES,
    }
    
    return render(request, 'admin/events_list.html', context)


@staff_member_required
def admin_users_list(request):
    """Список всіх користувачів для адміна"""
    users = User.objects.annotate(
        events_count=Count('organized_events'),
        rsvps_count=Count('rsvp_set')
    ).order_by('-date_joined')
    
    context = {
        'users': users,
    }
    
    return render(request, 'admin/users_list.html', context)


@staff_member_required
def admin_rsvps_list(request):
    """Список всіх RSVP для адміна"""
    rsvps = RSVP.objects.select_related('user', 'event').order_by('-created_at')
    
    context = {
        'rsvps': rsvps,
    }
    
    return render(request, 'admin/rsvps_list.html', context)