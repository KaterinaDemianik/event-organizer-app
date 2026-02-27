# Патерни проектування в Event Organizer App

## Огляд

Цей проект демонструє практичне застосування **10 патернів проектування**, які **реально використовуються в runtime-коді** для створення масштабованого та підтримуваного веб-додатку.

---

## 1. Specification Pattern (Патерн Специфікація)

**Файл:** `events/specifications.py`

**Використання:** `events/ui_views.py` (EventListView.get_queryset)

**Призначення:** Інкапсулює бізнес-правила фільтрації у окремі об'єкти, які можна комбінувати через функцію `apply_specifications()`.

**Реалізація:** Кожна специфікація має метод `to_queryset_filter()` що повертає Django Q-об'єкт. Комбінування специфікацій відбувається через функцію `apply_specifications()` яка об'єднує їх через логічне AND.

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

**Використання:** `events/ui_views.py` (EventListView.get_queryset)

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
- `event_pre_save` — зберігає попередній стан події для порівняння
- `event_post_save` — обробляє зміну статусу на `cancelled` (створює сповіщення учасникам про скасування)
- `rsvp_created` — сповіщає організатора про нову реєстрацію
- `rsvp_deleted` — сповіщає організатора про скасування реєстрації

**Важливо:** Сигнал `event_post_save` реагує саме на перехід до статусу `cancelled`, а не `archived`. Архівування подій відбувається через `EventArchiveService` без автоматичних сповіщень.

**Приклад:**

```python
@receiver(post_save, sender=RSVP)
def rsvp_created(sender, instance, created, **kwargs):
    if created:
        # Сповіщення організатору про нову реєстрацію через фабрику
        context = {
            'event': instance.event,
            'participant': instance.user
        }
        NotificationFactoryRegistry.create_notification(
            notification_type=Notification.RSVP_CONFIRMED,
            user=instance.event.organizer,
            event=instance.event,
            context=context
        )
```

**Переваги:**
- Слабке зчеплення: компоненти не залежать один від одного
- Розширюваність: легко додавати нові обробники подій
- Автоматизація: сповіщення створюються автоматично

---

## 4. Singleton Pattern (Патерн Одинак)

**Файл:** `events/services.py`

**Використання:** `events/ui_views.py` (EventListView.get_queryset)

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
        """Переводить завершені опубліковані події в архів"""
        now = timezone.now()
        queryset = Event.objects.filter(
            status=Event.PUBLISHED,
            ends_at__lt=now,
        )
        count = queryset.count()
        if count:
            queryset.update(status=Event.ARCHIVED)
        return count
```

**Переваги:**
- Централізований доступ до сервісу
- Контроль над ресурсами
- Узгоджене виконання операцій

---

## 5. Decorator Pattern (Патерн Декоратор)

**Файли:** `events/decorators.py`, `events/schedule_services.py`

**Використання:** 
- `events/ui_views.py` (rsvp_view, event_cancel_view, CalendarView)

**Призначення:** Динамічне додавання функціональності без зміни базового коду.

### 5.1 Декоратори функцій (Access Control)

**Реалізовані декоратори:**
- `@organizer_required` — перевірка, чи користувач є організатором
- `@event_not_archived` — заборона дій з архівними подіями
- `@event_not_cancelled` — заборона дій зі скасованими подіями
- `@event_not_started` — заборона дій з подіями, що вже розпочались

### 5.2 Декоратори розкладу (Schedule Wrappers)

**Реалізовані обгортки:**
- `BaseScheduleProvider` — базовий провайдер (адаптер до PersonalScheduleService)
- `FilteredScheduleDecorator` — фільтрація за параметрами (upcoming, organized, published)
- `HighlightedScheduleDecorator` — підсвічування подій (soon, organizer, popular)

**Приклад використання (CalendarView):**

```python
# Побудова ланцюжка декораторів
provider = BaseScheduleProvider()
provider = FilteredScheduleDecorator(provider, only_upcoming=True)
provider = HighlightedScheduleDecorator(provider, highlight_mode="soon")

entries = provider.get_entries(user)  # Відфільтровані та підсвічені
```

**GET-параметри календаря:**
- `?schedule_filter=upcoming` — тільки майбутні події
- `?schedule_filter=organized` — тільки мої організовані
- `?highlight=soon` — підсвітити події в межах 24 годин
- `?highlight=organizer` — підсвітити де я організатор

**Переваги:**
- Чистий код: логіка фільтрації/підсвічування відокремлена
- Повторне використання: декоратори можна комбінувати в ланцюжок
- Open/Closed: базовий сервіс не змінюється

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
        """Додаємо анотацію з кількістю RSVP до кожної події"""
        from django.db.models import Q
        return Event.objects.annotate(
            rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True)
        ).order_by("-starts_at")
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
        context = {'event': event}
        return NotificationService.notify_event_participants_with_factory(
            event, 
            Notification.EVENT_CANCELLED, 
            context
        )
```

**Переваги:**
- Менше дублювання логіки
- Краще структурування коду
- Легше тестувати бізнес-логіку

---

## 8. Factory Pattern (Патерн Фабрика)

**Файли:** `notifications/factories.py`

**Використання:** `events/signals.py`, `notifications/services.py`

**Призначення:** Централізоване створення об'єктів нотифікацій з уніфікованими шаблонами повідомлень.

**Реалізовані фабрики:**
- `EventUpdatedNotificationFactory` — загальні оновлення події
- `EventTimeChangedNotificationFactory` — зміна часу події
- `EventLocationChangedNotificationFactory` — зміна локації події
- `EventCancelledNotificationFactory` — скасування події
- `RSVPConfirmedNotificationFactory` — підтвердження реєстрації
- `RSVPCancelledNotificationFactory` — скасування реєстрації

**Приклад:**

```python
# Створення нотифікації через фабрику
context = {
    'event': event,
    'participant': user
}
NotificationFactoryRegistry.create_notification(
    notification_type=Notification.RSVP_CONFIRMED,
    user=organizer,
    event=event,
    context=context
)
```

**Переваги:**
- Централізація шаблонів повідомлень
- Зменшення дублювання коду
- Легкість додавання нових типів нотифікацій
- Уніфіковане форматування повідомлень

---

## 9. State Pattern (Патерн Стан)

**Файли:** `events/states.py`, `events/serializers.py`

**Використання:** 
- `events/ui_views.py` (EventUpdateView, event_cancel_view)
- `events/services.py` (archive_event)
- `events/serializers.py` (валідація переходів через API)

**Призначення:** Управління переходами між станами події (draft → published → cancelled/archived) з валідацією бізнес-правил як в UI, так і в API.

**Уніфікація для API:** Валідація переходів статусів реалізована в `EventSerializer` через методи `validate_status()` та `validate()`, які викликають `EventStateManager.validate_transition()`. Це блокує прямі зміни статусу через API, забезпечуючи дотримання правил State Pattern.

**Реалізовані стани:**
- `DraftState` — чернетка (можна редагувати, публікувати)
- `PublishedState` — опублікована (можна редагувати, скасувати, архівувати)
- `CancelledState` — скасована (жодних дій)
- `ArchivedState` — архівована (жодних дій)

**Приклад використання (UI):**

```python
from events.states import EventStateManager

# Перевірка можливості редагування
if not EventStateManager.can_edit(event):
    messages.error(request, "Цю подію не можна редагувати")

# Валідація переходу з бізнес-правилами
is_valid, error = EventStateManager.validate_transition(event, "archived")
if not is_valid:
    return False, error

# Отримання доступних дій
actions = EventStateManager.get_available_actions(event)
# ['edit', 'cancel', 'archive'] для завершеної опублікованої події
```

**Приклад використання (API через Serializer):**

```python
# events/serializers.py
def validate_status(self, value):
    if self.instance is None:
        return value
    
    is_valid, error_message = EventStateManager.validate_transition(
        self.instance, value
    )
    
    if not is_valid:
        raise serializers.ValidationError(error_message)
    
    return value
```

**Дозволені переходи:**
- `draft` → `published`, `cancelled`
- `published` → `cancelled`, `archived`
- `cancelled` → (жодних переходів)
- `archived` → (жодних переходів)

**Переваги:**
- Інкапсуляція логіки станів у окремих класах
- Валідація переходів з бізнес-правилами
- Легке додавання нових станів
- Чистий код без розгалужень if/elif

---

## 10. DTO Pattern (Data Transfer Object)

**Файл:** `events/schedule_services.py`

**Використання:** `events/ui_views.py` (CalendarView)

**Призначення:** Інкапсуляція даних для передачі між шарами додатку, уникаючи передачі ORM-об'єктів.

**Реалізовані компоненти:**
- `ScheduleEntry` — dataclass для запису в розкладі
- `PersonalScheduleService` — сервіс для формування персонального розкладу

**Приклад використання:**

```python
from events.schedule_services import PersonalScheduleService, ScheduleEntry

# Отримання розкладу користувача
entries = PersonalScheduleService.get_user_schedule_entries(user)
for entry in entries:
    print(f"{entry.title} - {entry.starts_at}")
    print(f"Організатор: {entry.is_organizer}")

# JSON для календаря
json_data = PersonalScheduleService.get_schedule_json_data(user)
```

**Оптимізація N+1:**
```python
# Один запит для подій, один для RSVP IDs
rsvp_event_ids = PersonalScheduleService.get_user_rsvp_event_ids(user)
# Замість .exists() в циклі — перевірка в множині
has_rsvp = event.id in rsvp_event_ids
```

**Переваги:**
- Відокремлення доменного шару від presentation
- Оптимізація запитів (уникнення N+1)
- Типізовані дані через dataclass
- Проста серіалізація в JSON

---

## Структура файлів з патернами

```
events/
├── specifications.py      # Specification Pattern
├── strategies.py          # Strategy Pattern
├── signals.py             # Observer Pattern
├── services.py            # Singleton + Service Layer
├── states.py              # State Pattern
├── schedule_services.py   # DTO Pattern + Service Layer
├── decorators.py          # Decorator Pattern
├── views.py               # Facade Pattern (API)
└── ui_views.py            # Facade Pattern (UI)

notifications/
├── factories.py           # Factory Pattern
└── services.py            # Service Layer Pattern
```

---

## Переваги використання патернів

1. **Чистий код** — кожен компонент має чітку відповідальність
2. **Тестованість** — легко тестувати кожен компонент ізольовано
3. **Гнучкість** — легко додавати нові функції без зміни існуючого коду
4. **Підтримуваність** — код легше читати і розуміти
5. **Масштабованість** — архітектура готова до розширення
6. **Оптимізація** — уникнення N+1 проблеми через DTO

---

## Додаткові ресурси

- [Specification Pattern](https://en.wikipedia.org/wiki/Specification_pattern)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Observer Pattern](https://refactoring.guru/design-patterns/observer)
- [State Pattern](https://refactoring.guru/design-patterns/state)
- [DTO Pattern](https://martinfowler.com/eaaCatalog/dataTransferObject.html)
- [Django Signals](https://docs.djangoproject.com/en/5.2/topics/signals/)
