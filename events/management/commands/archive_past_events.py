from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event


class Command(BaseCommand):
    help = 'Архівує завершені події'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Знаходимо всі опубліковані події, які вже завершились
        past_events = Event.objects.filter(
            status=Event.PUBLISHED,
            ends_at__lt=now
        )
        
        count = past_events.count()
        
        if count > 0:
            # Переводимо їх в архів
            past_events.update(status=Event.ARCHIVED)
            self.stdout.write(
                self.style.SUCCESS(f'Успішно архівовано {count} подій')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Немає подій для архівування')
            )
