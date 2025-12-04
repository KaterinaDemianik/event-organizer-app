"""
Management команда для виправлення дублікатів RSVP.
Видаляє старі записи, залишаючи тільки найновіші з status='going'.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from tickets.models import RSVP


class Command(BaseCommand):
    help = "Видаляє дублікати RSVP, залишаючи тільки найновіші записи"

    def handle(self, *args, **options):
        # Знайти всі комбінації user+event, які мають більше 1 запису
        duplicates = (
            RSVP.objects
            .values('user', 'event')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        total_deleted = 0
        
        for dup in duplicates:
            user_id = dup['user']
            event_id = dup['event']
            
            # Отримати всі RSVP для цієї комбінації
            rsvps = RSVP.objects.filter(
                user_id=user_id,
                event_id=event_id
            ).order_by('-created_at')
            
            # Залишити тільки найновіший
            latest = rsvps.first()
            old_rsvps = rsvps.exclude(id=latest.id)
            
            count = old_rsvps.count()
            old_rsvps.delete()
            total_deleted += count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Видалено {count} старих RSVP для user={user_id}, event={event_id}"
                )
            )
        
        # Також видалити всі RSVP з невалідним статусом
        invalid_rsvps = RSVP.objects.exclude(status='going')
        invalid_count = invalid_rsvps.count()
        
        if invalid_count > 0:
            invalid_rsvps.delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Видалено {invalid_count} RSVP з невалідним статусом"
                )
            )
            total_deleted += invalid_count
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n Всього видалено {total_deleted} записів RSVP"
            )
        )
