# Патерни проектування в Event Organizer App

## Огляд

Цей проект демонструє практичне застосування **7 патернів проектування**, які **реально використовуються в runtime-коді** для створення масштабованого та підтримуваного веб-додатку.

---

## 1. Specification Pattern (Патерн Специфікація)

**Файл:** `events/specifications.py`

**Використання:** `events/ui_views.py` (EventListView, рядки 286-300)

**Призначення:** Інкапсулює бізнес-правила фільтрації у окремі об'єкти, які можна комбінувати через логічні операції (AND, OR, NOT).

**Приклад використання:**

```python
from events.specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    EventByLocationSpecification,
    apply_specifications,
)

# Створення специфікацій
specs = []
if q:
    specs.append(EventByTitleSpecification(q))
if status:
    specs.append(EventByStatusSpecification(status))
if location:
    specs.append(EventByLocationSpecification(location))

# Застосування до QuerySet
filtered_qs = apply_specifications(qs, *specs)
```

**Переваги:**
- Чистий код: бізнес-логіка відокремлена від інфраструктури
- Повторне використання: специфікації можна комбінувати
- Тестованість: кожну специфікацію легко тестувати окремо

---

## 2. Strategy Pattern (Патерн Стратегія)

**Файл:** `events/strategies.py`

**Використання:** `events/ui_views.py` (EventListView.get_queryset, рядки 353-358)

**Призначення:** Визначає сімейство алгоритмів сортування і робить їх взаємозамінними.

**Реалізовані стратегії:**
- `SortByDateStrategy` — сортування за датою
- `SortByPopularityStrategy` — сортування за популярністю
- `SortByAlphabetStrategy` — сортування за абеткою
- `SortByEventDateStrategy` — сортування за датою події
- `SortByRsvpCountStrategy` — сортування за кількістю учасників

**Приклад використання:**

```python
from events.strategies import get_sort_strategy

sort_slug = request.GET.get("sort", "date")
strategy = get_sort_strategy(sort_slug)
sorted_qs = strategy.sort(queryset)
```

**Переваги:**
- Гнучкість: легко додавати нові алгоритми сортування
- Централізація: вся логіка сортування в одному місці
- Чистий код: немає розгалужень if/elif в основному коді

---

## 3. Observer Pattern (Патерн Спостерігач)

**Файл:** `events/signals.py`

**Використання:** Автоматично підключається через `events/apps.py`

**Призначення:** Реагування на зміни в подіях та RSVP без жорстких залежностей між компонентами.

**Реалізовані сигнали:**
- `event_pre_save` — зберігає попередній стан події
- `event_post_save` — обробляє зміни статусу (скасування, архівування)
- `rsvp_created` — сповіщає організатора про нову реєстрацію
- `rsvp_deleted` — сповіщає організатора про скасування реєстрації

**Приклад:**

```python
@receiver(post_save, sender=RSVP)
def rsvp_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.event.organizer,
            event=instance.event,
            notification_type=Notification.RSVP_CONFIRMED,
            message=f"Користувач {instance.user.username} зареєструвався"
        )
```

**Переваги:**
- Слабке зчеплення: компоненти не залежать один від одного
- Розширюваність: легко додавати нові обробники подій
- Автоматизація: сповіщення створюються автоматично

---

## 4. Singleton Pattern (Патерн Одинак)

**Файл:** `events/services.py`

**Використання:** `events/ui_views.py` (EventListView.get_queryset, рядок 242)

**Призначення:** Забезпечує єдиний екземпляр сервісу архівування подій.

**Реалізація:**

```python
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class EventArchiveService(metaclass=SingletonMeta):
    def archive_past_events(self) -> int:
        # Архівує завершені події
        pass
```

**Переваги:**
- Централізований доступ до сервісу
- Контроль над ресурсами
- Узгоджене виконання операцій

---

## 5. Decorator Pattern (Патерн Декоратор)

**Файл:** `events/decorators.py`

**Використання:** `events/ui_views.py` (rsvp_view, rsvp_cancel_view, event_cancel_view, event_participants_view)

**Призначення:** Динамічне додавання перевірок доступу до функцій без зміни їх коду.

**Реалізовані декоратори:**
- `@organizer_required` — перевірка, чи користувач є організатором
- `@event_not_archived` — заборона дій з архівними подіями
- `@event_not_cancelled` — заборона дій зі скасованими подіями
- `@event_not_started` — заборона дій з подіями, що вже розпочались

**Приклад використання:**

```python
@login_required
@organizer_required
@event_not_archived
def event_cancel_view(request, pk: int):
    event = request.event  # Отримуємо з декоратора
    # Логіка скасування
```

**Переваги:**
- Чистий код: логіка перевірок відокремлена
- Повторне використання: декоратори можна комбінувати
- DRY: немає дублювання перевірок у кожній функції

---

## 6. Facade Pattern (Патерн Фасад)

**Файли:** `events/views.py`, `events/ui_views.py`

**Використання:** API та UI endpoints

**Призначення:** Надає спрощений інтерфейс до складної підсистеми (моделі, специфікації, стратегії, сервіси).

**Приклад:**

```python
class EventViewSet(viewsets.ModelViewSet):
    """Фасад для API — приховує складність внутрішньої логіки"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def get_queryset(self):
        # Внутрішня логіка фільтрації, сортування, анотацій
        pass
```

**Переваги:**
- Приховує внутрішню складність
- Спрощує використання API
- Єдина точка входу для клієнтів

---

## 7. Service Layer Pattern (Патерн Сервісний Шар)

**Файли:** `events/services.py`, `notifications/services.py`

**Використання:** `events/ui_views.py`, `events/signals.py`

**Призначення:** Винесення бізнес-логіки з контролерів у окремі сервіси.

**Реалізовані сервіси:**
- `EventArchiveService` — архівування завершених подій
- `NotificationService` — створення сповіщень для учасників

**Приклад:**

```python
class NotificationService:
    @staticmethod
    def create_event_cancelled_notification(event):
        """Створює сповіщення про скасування події"""
        message = f"Подія '{event.title}' була скасована."
        return NotificationService.notify_event_participants(
            event, Notification.EVENT_CANCELLED, message
        )
```

**Переваги:**
- Менше дублювання логіки
- Краще структурування коду
- Легше тестувати бізнес-логіку

---

## Структура файлів з патернами

```
events/
├── specifications.py    # Specification Pattern
├── strategies.py        # Strategy Pattern
├── signals.py           # Observer Pattern
├── services.py          # Singleton + Service Layer
├── decorators.py        # Decorator Pattern
├── views.py             # Facade Pattern (API)
└── ui_views.py          # Facade Pattern (UI)

notifications/
└── services.py          # Service Layer Pattern
```

---

## Переваги використання патернів

1. **Чистий код** — кожен компонент має чітку відповідальність
2. **Тестованість** — легко тестувати кожен компонент ізольовано
3. **Гнучкість** — легко додавати нові функції без зміни існуючого коду
4. **Підтримуваність** — код легше читати і розуміти
5. **Масштабованість** — архітектура готова до розширення

---

## Додаткові ресурси

- [Specification Pattern](https://en.wikipedia.org/wiki/Specification_pattern)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Observer Pattern](https://refactoring.guru/design-patterns/observer)
- [Django Signals](https://docs.djangoproject.com/en/5.2/topics/signals/)
