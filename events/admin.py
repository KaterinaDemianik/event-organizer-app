from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'location', 'starts_at', 'status', 'created_at')
    list_filter = ('status', 'starts_at', 'created_at')
    search_fields = ('title', 'description', 'location', 'organizer__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'starts_at'
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'description', 'organizer')
        }),
        ('Деталі події', {
            'fields': ('location', 'starts_at', 'ends_at', 'status')
        }),
        ('Метадані', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )