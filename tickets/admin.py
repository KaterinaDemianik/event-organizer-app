from django.contrib import admin
from .models import RSVP


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event', 'created_at']
    list_filter = ['created_at', 'event__status']
    search_fields = ['user__username', 'event__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'event')