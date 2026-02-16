#  Архітектурні патерни Event Organizer

## Огляд архітектури

Event Organizer використовує багаторівневу архітектуру з чіткою відповідальністю кожного шару.

---

## 1. MVT (Model-View-Template) - Django варіант MVC

Django використовує **MVT** замість класичного MVC:

### Порівняння MVC vs MVT

| MVC | MVT (Django) | Наш проект |
|-----|--------------|------------|
| **Model** | **Model** | `events/models.py` |
| **View** | **Template** | `templates/events/` |
| **Controller** | **View** | `events/ui_views.py` |

### Реалізація в проекті:

#### **Model (Модель)** - Бізнес-логіка та дані
```python
# events/models.py
class Event(models.Model):
    title = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    # ... інші поля
```

**Відповідальність:**
- Структура даних
- Валідація на рівні моделі
- Бізнес-логіка (методи моделі)

#### **View (Представлення)** - Логіка обробки запитів
```python
# events/ui_views.py
class EventListView(ListView):
    model = Event
    template_name = "events/list.html"
    
    def get_queryset(self):
        # Логіка фільтрації та сортування
        pass
```

**Відповідальність:**
- Обробка HTTP запитів
- Виклик бізнес-логіки
- Підготовка даних для шаблону

#### **Template (Шаблон)** - Відображення
```django
<!-- templates/events/list.html -->
{% for event in events %}
  <article>
    <h3>{{ event.title }}</h3>
    <p>{{ event.description }}</p>
  </article>
{% endfor %}
```

**Відповідальність:**
- Відображення HTML
- Презентаційна логіка
- UX/UI

---

## 2. Layered Architecture (Шарова архітектура)

```
┌─────────────────────────────────────┐
│   Presentation Layer (Templates)    │  ← Шаблони, UI
├─────────────────────────────────────┤
│   Application Layer (Views)         │  ← Контролери, бізнес-логіка
├─────────────────────────────────────┤
│   Domain Layer (Models, Services)   │  ← Моделі, сервіси
├─────────────────────────────────────┤
│   Data Access Layer (ORM)           │  ← Django ORM
├─────────────────────────────────────┤
│   Database (MySQL)                  │  ← Збереження даних
└─────────────────────────────────────┘
```

### Реалізація шарів:

#### **Presentation Layer**
```
templates/
├── base.html
├── events/
│   ├── list.html
│   ├── detail.html
│   └── create.html
└── registration/
    ├── login.html
    └── signup.html
```

#### **Application Layer**
```
events/
├── ui_views.py      # UI контролери
├── views.py         # API контролери
└── forms.py         # Валідація форм
```

#### **Domain Layer**
```
events/
├── models.py        # Доменні моделі
├── services.py      # Бізнес-логіка (Singleton + Service Layer)
├── specifications.py # Бізнес-правила (Specification)
├── strategies.py    # Алгоритми (Strategy)
├── signals.py       # Реакція на події (Observer)
└── decorators.py    # Контроль доступу (Decorator)
```

#### **Data Access Layer**
```
events/
└── models.py        # Django ORM
```

---

## 3. Service Layer Pattern

**Призначення:** Інкапсулює бізнес-логіку в окремі сервіси.

### Приклад: EventArchiveService

```python
# events/services.py
class EventArchiveService(metaclass=SingletonMeta):
    """Сервіс для архівування подій"""
    
    def archive_past_events(self) -> int:
        """Бізнес-логіка архівування"""
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
- Відокремлення бізнес-логіки від контролерів
- Повторне використання логіки
- Легше тестувати

---

## 4. Observer Pattern (Django Signals)

**Призначення:** Реагування на зміни в системі без жорстких залежностей.

### Реалізовано:

```python
# events/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Event)
def event_post_save(sender, instance, created, **kwargs):
    """Обробляє зміни в події після збереження"""
    if not created:
        # Перевіряємо зміну статусу на CANCELLED
        if instance.status == Event.CANCELLED:
            NotificationService.create_event_cancelled_notification(instance)

@receiver(post_save, sender=RSVP)
def rsvp_created(sender, instance, created, **kwargs):
    """Сповіщає організатора про нову реєстрацію"""
    if created:
        Notification.objects.create(
            user=instance.event.organizer,
            notification_type=Notification.RSVP_CONFIRMED,
            message=f"Новий учасник: {instance.user.username}"
        )
```

**Переваги:**
- Слабке зчеплення компонентів
- Автоматичне сповіщення без дублювання коду
- Легко додавати нові обробники

---

## 5. API Architecture (REST)

### RESTful endpoints:

```
GET    /api/events/          # Список подій
POST   /api/events/          # Створити подію
GET    /api/events/{id}/     # Деталі події
PUT    /api/events/{id}/     # Оновити подію
DELETE /api/events/{id}/     # Видалити подію
POST   /api/events/{id}/rsvp/ # RSVP на подію
```

### Архітектура API:

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ HTTP Request
       ▼
┌──────────────┐
│   ViewSet    │ ← events/views.py
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Serializer  │ ← events/serializers.py
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Model     │ ← events/models.py
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Database   │
└──────────────┘
```

---

## 6. Dependency Injection (Впровадження залежностей)

Django використовує DI через:

### Settings-based configuration:
```python
# settings.py
INSTALLED_APPS = [
    'events',
    'users',
    'tickets',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # ...
    }
}
```

### Middleware injection:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # ...
]
```

---

## 7. Front Controller Pattern

**Django URLconf** виступає як Front Controller:

```python
# event_organizer/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('events.urls')),
    path('accounts/', include('users.urls')),
    path('', include('events.ui_urls')),
]
```

**Переваги:**
- Централізована маршрутизація
- Middleware обробка
- Єдина точка входу

---

## 8. Template Method Pattern (в Class-Based Views)

```python
class EventListView(ListView):
    # Template method pattern
    
    def get_queryset(self):
        # Крок 1: Отримати дані
        pass
    
    def get_context_data(self, **kwargs):
        # Крок 2: Підготувати контекст
        pass
    
    def render_to_response(self, context):
        # Крок 3: Відрендерити відповідь
        pass
```

---

## 9. Observer Pattern (Signals)

Django Signals - реалізація Observer:

```python
# events/signals.py (концепт)
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Event)
def event_created(sender, instance, created, **kwargs):
    if created:
        # Відправити email організатору
        # Створити notification
        pass
```

---

## 10. Middleware Pattern (Chain of Responsibility)

```python
Request → SecurityMiddleware 
       → SessionMiddleware 
       → CsrfViewMiddleware 
       → AuthenticationMiddleware 
       → MessageMiddleware 
       → View
```

Кожен middleware може:
- Обробити запит
- Передати далі
- Повернути відповідь

---

## Діаграма повної архітектури

```
┌─────────────────────────────────────────────────────┐
│                    Browser/Client                    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP Request
                     ▼
┌─────────────────────────────────────────────────────┐
│              Django Front Controller                 │
│                  (URLconf)                           │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│  UI Views    │          │  API Views   │
│ (ui_views.py)│          │  (views.py)  │
└──────┬───────┘          └──────┬───────┘
       │                         │
       │                         ▼
       │                  ┌──────────────┐
       │                  │ Serializers  │
       │                  └──────┬───────┘
       │                         │
       └─────────┬───────────────┘
                 ▼
        ┌────────────────┐
        │   Services     │ ← Singleton
        │ Specifications │ ← Specification
        │   Strategies   │ ← Strategy
        └────────┬───────┘
                 ▼
        ┌────────────────┐
        │     Models     │ ← Domain Layer
        └────────┬───────┘
                 ▼
        ┌────────────────┐
        │  Django ORM    │ ← Data Access
        └────────┬───────┘
                 ▼
        ┌────────────────┐
        │  MySQL DB      │
        └────────────────┘
```

---

## Переваги нашої архітектури

1. **Separation of Concerns** - Кожен шар має свою відповідальність
2. **Testability** - Легко тестувати кожен компонент окремо
3. **Maintainability** - Зміни в одному шарі не впливають на інші
4. **Scalability** - Легко додавати нові функції
5. **Reusability** - Сервіси та специфікації можна використовувати повторно

---

## Використані патерни проектування

| Патерн | Реалізація | Файл |
|--------|------------|------|
| **MVT** | Django framework | Вся структура |
| **Layered** | Presentation/Application/Domain/Data | Структура папок |
| **Service Layer + Singleton** | `EventArchiveService` | `events/services.py` |
| **Specification** | Фільтрація подій через об'єкти-специфікації | `events/specifications.py` |
| **Strategy** | Стратегії сортування списку подій | `events/strategies.py` |
| **Observer** | Django Signals для сповіщень | `events/signals.py` |
| **Factory** | Централізоване створення нотифікацій | `notifications/factories.py` |
| **Decorator** | Декоратори контролю доступу | `events/decorators.py` |
| **REST API / Facade** | DRF ViewSets як фасад до доменного шару | `events/views.py` |
| **Front Controller** | URLconf | `event_organizer/urls.py` |
| **Template Method** | Class-Based Views | `events/ui_views.py` |

---

## Додаткові ресурси

- [Django MVT Architecture](https://docs.djangoproject.com/en/5.2/faq/general/#django-appears-to-be-a-mvc-framework-but-you-call-the-controller-the-view-and-the-view-the-template-how-come-you-don-t-use-the-standard-names)
- [Layered Architecture](https://en.wikipedia.org/wiki/Multitier_architecture)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [REST API Design](https://restfulapi.net/)