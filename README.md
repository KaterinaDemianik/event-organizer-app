# Event Organizer App 

Веб-додаток для організації та управління подіями з використанням патернів проєктування.

##  Про проект

**Курсова робота**  
**Автор:** Демʼянік Катерина

### Тема
Створення веб-додатку для організації подій із застосуванням патернів проєктування.

### Мета
Розробити веб-додаток для створення, перегляду та управління подіями з реалізацією основних функцій CRUD (створення, читання, оновлення, видалення) із застосуванням патернів проєктування для покращення структури та гнучкості коду.

### Ідея
Проєкт демонструє, як архітектурні підходи та шаблони проєктування допомагають створювати зручні, масштабовані та зрозумілі веб-застосунки.

## Технології

- **Backend:** Django 5.2.8, Python 3.13
- **Database:** MySQL 8.0
- **Frontend:** HTML5, CSS3, JavaScript
- **CSS Framework:** Pico CSS
- **API:** Django REST Framework

## Функціонал

-  Створення та управління подіями
-  Система реєстрації користувачів (RSVP)
- Автентифікація та авторизація
-  Фільтрація подій (всі, мої, заплановані)
-  Світла/темна тема
-  Адаптивний дизайн
-  Редагування подій організатором
-  Скасування подій

##  Встановлення

```bash
# Клонувати репозиторій
git clone https://github.com/KaterinaDemianik/event-organizer-app.git
cd event-organizer-app

# Встановити залежності
pip install -r requirements.txt

# Налаштувати базу даних (див. DATABASE_SETUP.md)
python manage.py migrate

# Завантажити тестові дані
python load_test_data.py

# Запустити сервер
python manage.py runserver
```

## Документація

- [ARCHITECTURE.md](ARCHITECTURE.md) - Архітектурні патерни (MVT, Layered, Service Layer)
- [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) - Патерни проєктування (Specification, Strategy, Singleton)
- [SECURITY.md](SECURITY.md) - Безпека та автентифікація (Argon2, Sessions, CSRF)
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Налаштування MySQL
- [ARCHIVE_INFO.md](ARCHIVE_INFO.md) - Система архівування подій

##  Патерни проєктування

### Реалізовано 11 патернів:

#### Поведінкові патерни:
- **Specification Pattern** – гнучка фільтрація подій (`events/specifications.py`)
- **Strategy Pattern** – стратегії сортування (`events/strategies.py`)
- **Observer Pattern** – Django Signals для подій системи

#### Креаційні патерни:
- **Factory Pattern** – створення подій різних типів (`events/factories.py`)
- **Builder Pattern** – поетапне створення складних подій (`events/builders.py`)
- **Singleton Pattern** – сервіс архівування (`events/services.py`)

#### Структурні патерни:
- **Decorator Pattern** – декоратори доступу (`events/decorators.py`)
- **Proxy Pattern** – управління сесіями (`users/session_manager.py`)
- **Facade Pattern** – спрощений інтерфейс API/UI (`events/views.py`, `events/ui_views.py`)

#### Архітектурні патерни:
- **Repository Pattern** – абстракція доступу до даних (`events/repositories.py`)
- **Service Layer Pattern** – бізнес-логіка в сервісах (`events/services.py`)

### Детальна документація:
Див. [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) для повного опису кожного патерну з прикладами коду.