#!/usr/bin/env python
"""
Скрипт для завантаження тестових даних в MySQL базу
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_organizer.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Event
from tickets.models import RSVP
from datetime import datetime, timedelta

User = get_user_model()

# Створюємо тестових користувачів
print("Створюємо користувачів...")
katerina, _ = User.objects.get_or_create(
    username='Katerina_demianik',
    defaults={'email': 'katerina@example.com'}
)
katerina.set_password('password123')
katerina.save()

user2, _ = User.objects.get_or_create(
    username='ivan_petrov',
    defaults={'email': 'ivan@example.com'}
)
user2.set_password('password123')
user2.save()

print(f"✓ Користувачі створені: {katerina.username}, {user2.username}")

# Створюємо події
print("\nСтворюємо події...")
now = datetime.now()

event1, _ = Event.objects.get_or_create(
    title="Волонтерство",
    defaults={
        'description': "допомога літнім маломобільним людям",
        'location': "Київ",
        'starts_at': now + timedelta(days=5),
        'ends_at': now + timedelta(days=5, hours=4),
        'status': Event.PUBLISHED,
        'organizer': katerina,
    }
)

event2, _ = Event.objects.get_or_create(
    title="Конференція з веб-розробки",
    defaults={
        'description': "Сучасні технології та тренди в веб-розробці. Доповіді від провідних експертів.",
        'location': "Львів",
        'starts_at': now + timedelta(days=10),
        'ends_at': now + timedelta(days=10, hours=8),
        'status': Event.PUBLISHED,
        'organizer': user2,
    }
)

event3, _ = Event.objects.get_or_create(
    title="Майстер-клас з дизайну",
    defaults={
        'description': "UI/UX дизайн для початківців",
        'location': "Одеса",
        'starts_at': now + timedelta(days=15),
        'ends_at': now + timedelta(days=15, hours=3),
        'status': Event.DRAFT,
        'organizer': katerina,
    }
)

print(f"✓ Події створені: {event1.title}, {event2.title}, {event3.title}")

# Створюємо RSVP
print("\nСтворюємо реєстрації...")
rsvp1, created1 = RSVP.objects.get_or_create(user=katerina, event=event1)
rsvp2, created2 = RSVP.objects.get_or_create(user=user2, event=event1)
rsvp3, created3 = RSVP.objects.get_or_create(user=katerina, event=event2)

print(f"✓ RSVP створені: {Event.objects.count()} подій, {RSVP.objects.count()} реєстрацій")

print("\n" + "="*50)
print("✅ Тестові дані успішно завантажені!")
print("="*50)
print("\nДані для входу:")
print("  Суперкористувач: admin / admin123")
print("  Користувач 1: Katerina_demianik / password123")
print("  Користувач 2: ivan_petrov / password123")
print("\nЗапустіть сервер: python manage.py runserver")
