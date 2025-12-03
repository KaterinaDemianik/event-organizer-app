from django.core.management.base import BaseCommand
from events.services import EventArchiveService


class Command(BaseCommand):
    help = 'Архівує завершені події'

    def handle(self, *args, **options):
        service = EventArchiveService()
        count = service.archive_past_events()

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Успішно архівовано {count} подій'))
        else:
            self.stdout.write(self.style.WARNING('Немає подій для архівування'))