from django.contrib.admin import AdminSite
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from tickets.models import RSVP
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAdminSite(AdminSite):
    site_header = "Event Organizer Admin"
    site_title = "Admin Panel"
    index_title = "Панель управління"

    def index(self, request, extra_context=None):
        """Додаємо статистику до головної сторінки"""
        
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        extra_context = extra_context or {}
        
        extra_context.update({
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
        })
        
        extra_context['top_events'] = Event.objects.annotate(
            rsvp_count=Count('rsvps')
        ).order_by('-rsvp_count')[:5]
        
        extra_context['recent_events'] = Event.objects.order_by('-created_at')[:5]
        
        extra_context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        
        extra_context['recent_rsvps'] = RSVP.objects.select_related(
            'user', 'event'
        ).order_by('-created_at')[:10]
        
        return super().index(request, extra_context)