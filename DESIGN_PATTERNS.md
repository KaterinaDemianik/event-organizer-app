# Design Patterns в Event Organizer App

## Реалізовані патерни

### 1. **Specification Pattern** (Патерн Специфікація)

**Файл:** `events/specifications.py`

**Призначення:** Інкапсулює бізнес-правила фільтрації у окремі об'єкти, які можна комбінувати.

**Переваги:**
- Чистий код: бізнес-логіка відокремлена від інфраструктури
- Переваги повторного використання: специфікації можна комбінувати
- Тестованість: кожну специфікацію легко тестувати окремо
- Гнучкість: легко додавати нові умови фільтрації

**Приклад використання:**

```python
from events.specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    PublishedEventsSpecification,
    UpcomingEventsSpecification,
)

# Проста специфікація
published_spec = PublishedEventsSpecification()

# Комбінування специфікацій через AND
published_and_upcoming = PublishedEventsSpecification() & UpcomingEventsSpecification()

# Комбінування через OR
draft_or_cancelled = EventByStatusSpecification('draft') | EventByStatusSpecification('cancelled')

# Інверсія (NOT)
not_published = ~PublishedEventsSpecification()

# Застосування до QuerySet
from events.specifications import apply_specifications
filtered_events = apply_specifications(
    Event.objects.all(),
    published_spec,
    EventByTitleSpecification('конференція')
)
```

**Реалізовані специфікації:**
- `EventByStatusSpecification` - фільтрація за статусом
- `EventByTitleSpecification` - пошук за назвою
- `EventByLocationSpecification` - пошук за місцем
- `EventByDateRangeSpecification` - фільтрація за діапазоном дат
- `PublishedEventsSpecification` - тільки опубліковані події
- `UpcomingEventsSpecification` - майбутні події

**Використання у проекті:**
- `events/ui_views.py` - EventListView використовує специфікації для фільтрації
- `events/views.py` - API ViewSet імпортує специфікації (готово до використання)

---

### 2. **Repository Pattern** (Патерн Репозиторій)

**Статус:** Підготовлено до реалізації

**Призначення:** Абстрагує доступ до даних, надаючи колекціє-подібний інтерфейс.

**План реалізації:**

```python
# events/repositories.py (майбутній файл)

class EventRepository:
    """Репозиторій для роботи з подіями"""
    
    def get_by_id(self, event_id: int) -> Event:
        return Event.objects.get(pk=event_id)
    
    def get_all(self) -> QuerySet:
        return Event.objects.all()
    
    def find_by_specification(self, spec: Specification) -> QuerySet:
        return Event.objects.filter(spec.to_queryset_filter())
    
    def save(self, event: Event) -> Event:
        event.save()
        return event
    
    def delete(self, event: Event):
        event.delete()
```

---

### 3. **Unit of Work Pattern** (Патерн Одиниця Роботи)

**Статус:** Підготовлено до реалізації

**Призначення:** Координує зміни в кількох агрегатах і забезпечує транзакційність.

**План реалізації:**

```python
# core/unit_of_work.py (майбутній файл)

from django.db import transaction

class UnitOfWork:
    """Координує транзакції між репозиторіями"""
    
    def __enter__(self):
        self.transaction = transaction.atomic()
        self.transaction.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return self.transaction.__exit__(exc_type, exc_val, exc_tb)
    
    def commit(self):
        pass  # Django автоматично комітить при виході з atomic()
    
    def rollback(self):
        pass  # Django автоматично робить rollback при помилці
```

---

### 4. **Strategy Pattern** (Патерн Стратегія)

**Статус:** Підготовлено до реалізації

**Призначення:** Визначає сімейство алгоритмів і робить їх взаємозамінними.

**Приклад використання (сортування подій):**

```python
# events/strategies.py (майбутній файл)

from abc import ABC, abstractmethod

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, queryset):
        pass

class SortByDateStrategy(SortStrategy):
    def sort(self, queryset):
        return queryset.order_by('-starts_at')

class SortByPopularityStrategy(SortStrategy):
    def sort(self, queryset):
        return queryset.annotate(
            rsvp_count=Count('rsvps')
        ).order_by('-rsvp_count')

class SortByTitleStrategy(SortStrategy):
    def sort(self, queryset):
        return queryset.order_by('title')
```

---

### 5. **Observer Pattern** (Патерн Спостерігач)

**Статус:** Частково реалізовано через Django Signals

**Призначення:** Визначає залежність один-до-багатьох між об'єктами.

**Використання в Django:**
- Django Signals (`pre_save`, `post_save`, `pre_delete`, `post_delete`)
- Можна додати кастомні сигнали для подій (наприклад, `event_published`, `rsvp_created`)

**Приклад розширення:**

```python
# events/signals.py (майбутній файл)

from django.dispatch import Signal, receiver
from django.core.mail import send_mail

# Кастомний сигнал
event_published = Signal()

@receiver(event_published)
def notify_subscribers(sender, event, **kwargs):
    """Сповіщає підписників про нову подію"""
    # Логіка відправки email/push-сповіщень
    pass
```

---

### 6. **Factory Pattern** (Патерн Фабрика)

**Статус:** Підготовлено до реалізації

**Призначення:** Створює об'єкти без вказівки точного класу.

**Приклад (фабрика для створення подій різних типів):**

```python
# events/factories.py (майбутній файл)

class EventFactory:
    """Фабрика для створення подій"""
    
    @staticmethod
    def create_conference(title, organizer, **kwargs):
        return Event.objects.create(
            title=title,
            organizer=organizer,
            event_type='conference',
            **kwargs
        )
    
    @staticmethod
    def create_workshop(title, organizer, **kwargs):
        return Event.objects.create(
            title=title,
            organizer=organizer,
            event_type='workshop',
            **kwargs
        )
```

---

### 7. **Facade Pattern** (Патерн Фасад)

**Статус:** Реалізовано в API ViewSet

**Призначення:** Надає спрощений інтерфейс до складної підсистеми.

**Приклад:**
- `EventViewSet` у `events/views.py` - фасад для API
- `EventListView` у `events/ui_views.py` - фасад для UI

Ці класи приховують складність роботи з моделями, специфікаціями, пагінацією тощо.

---

### 8. **CQRS (Command Query Responsibility Segregation)**

**Статус:** Підготовлено до реалізації

**Призначення:** Розділяє операції читання і запису.

**План реалізації:**

```python
# events/commands.py (майбутній файл)

class CreateEventCommand:
    def __init__(self, title, organizer, starts_at, ends_at, **kwargs):
        self.title = title
        self.organizer = organizer
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.kwargs = kwargs

class CreateEventHandler:
    def handle(self, command: CreateEventCommand) -> Event:
        return Event.objects.create(
            title=command.title,
            organizer=command.organizer,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            **command.kwargs
        )

# events/queries.py (майбутній файл)

class GetUpcomingEventsQuery:
    def __init__(self, limit=10):
        self.limit = limit

class GetUpcomingEventsHandler:
    def handle(self, query: GetUpcomingEventsQuery):
        spec = UpcomingEventsSpecification() & PublishedEventsSpecification()
        return apply_specifications(
            Event.objects.all(), spec
        )[:query.limit]
```

---

## Поточний стан реалізації

### ✅ Реалізовано:
1. **Specification Pattern** - повністю реалізовано і використовується
2. **Facade Pattern** - використовується в ViewSets
3. **Observer Pattern** - частково через Django Signals

### 🔄 Підготовлено до реалізації:
4. **Repository Pattern**
5. **Unit of Work Pattern**
6. **Strategy Pattern**
7. **Factory Pattern**
8. **CQRS Pattern**

---

## Як додати нові патерни

### Крок 1: Repository Pattern

1. Створити `events/repositories.py`
2. Реалізувати `EventRepository` і `RSVPRepository`
3. Оновити views для використання репозиторіїв замість прямих ORM-запитів

### Крок 2: Unit of Work Pattern

1. Створити `core/unit_of_work.py`
2. Інтегрувати з репозиторіями
3. Використовувати в складних транзакціях (наприклад, створення події + автоматичний RSVP організатора)

### Крок 3: Strategy Pattern

1. Створити `events/strategies.py`
2. Реалізувати стратегії сортування
3. Додати параметр `ordering` до API і UI

---

## Тестування патернів

### Specification Pattern

```python
# tests/test_specifications.py

from events.specifications import EventByStatusSpecification, PublishedEventsSpecification
from events.models import Event

def test_status_specification():
    spec = EventByStatusSpecification('published')
    event = Event(status='published')
    assert spec.is_satisfied_by(event) == True

def test_combined_specifications():
    spec = PublishedEventsSpecification() & UpcomingEventsSpecification()
    # Тестування комбінованої специфікації
```

---

## Переваги використання патернів у проекті

1. **Чистий код:** Бізнес-логіка відокремлена від інфраструктури
2. **Тестованість:** Кожен компонент легко тестувати ізольовано
3. **Гнучкість:** Легко додавати нові функції без зміни існуючого коду
4. **Підтримуваність:** Код легше читати і розуміти
5. **Масштабованість:** Архітектура готова до розширення

---

### 9. **Decorator Pattern** (Патерн Декоратор)

**Статус:** ✅ Реалізовано

**Призначення:** Динамічно додає нову функціональність до об'єктів.

**Файл:** `events/decorators.py`

**Приклад:**
```python
@login_required
@organizer_required
def event_cancel_view(request, pk):
    # Тільки організатор може скасувати подію
    pass
```

---

### 10. **Proxy Pattern** (Патерн Замісник)

**Статус:** ✅ Реалізовано

**Призначення:** Надає замінник для управління доступом до об'єкта.

**Файл:** `users/session_manager.py`

**Приклад:**
```python
session_mgr = SessionManager(request)
session_mgr.add_to_history(event_id)
```

---

## Додаткові ресурси

- [Specification Pattern](https://en.wikipedia.org/wiki/Specification_pattern)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- [Django Design Patterns](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)
- [SECURITY.md](SECURITY.md) - Детальна документація з безпеки
