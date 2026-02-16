# Безпека Event Organizer App

## Огляд системи безпеки

Event Organizer використовує багаторівневий підхід до безпеки з використанням вбудованих механізмів Django та патернів проєктування.

---

## Автентифікація та паролі

### Хешування паролів

**Алгоритм:** Argon2id (переможець Password Hashing Competition 2015)

**Чому Argon2?**
- Рекомендовано OWASP
- Найкращий захист від GPU/ASIC атак
- Використовує багато пам'яті (важко атакувати)
- Налаштування memory, time, parallelism

**Формат збереження:**
```
argon2$argon2id$v=19$m=102400,t=2,p=8$salt$hash
```

- **Алгоритм:** `argon2id` (гібрид argon2i та argon2d)
- **Версія:** v=19
- **Параметри:**
  - `m=102400` - пам'ять (100 MB)
  - `t=2` - ітерації
  - `p=8` - паралелізм (потоки)
- **Сіль (salt):** Унікальна для кожного пароля
- **Хеш:** Результат обчислення

**Приклад з бази даних:**
```
argon2$argon2id$v=19$m=102400,t=2,p=8$c29tZXNhbHQ$hash...
```

**Fallback алгоритми:**
- PBKDF2-SHA256 (для старих паролів)
- BCrypt (для міграції з інших систем)

### Налаштування в settings.py

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Основний
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Fallback
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',  # Fallback
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**Валідація паролів:**
- Мінімум 8 символів
- Не схожий на username/email
- Не з списку найпоширеніших паролів
- Не тільки цифри

---

## Управління сесіями

### Конфігурація сесій

```python
# settings.py
SESSION_COOKIE_AGE = 1209600  # 2 тижні
SESSION_COOKIE_HTTPONLY = True  # Захист від XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # Захист від CSRF
SESSION_SAVE_EVERY_REQUEST = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# SESSION_COOKIE_SECURE = True  # Увімкнути для HTTPS в production
```

### Зберігання сесій

**Backend:** Database-backed sessions (таблиця `django_session`)

**Структура:**
- `session_key` - Унікальний ідентифікатор
- `session_data` - Зашифровані дані (JSON)
- `expire_date` - Дата закінчення

**Автоматичне очищення:**
```bash
python manage.py clearsessions
```

---

## CSRF захист

### Cross-Site Request Forgery Protection

**Механізм:**
1. Django генерує унікальний CSRF токен для кожної сесії
2. Токен додається до всіх форм через `{% csrf_token %}`
3. При POST запиті перевіряється відповідність токенів

**Налаштування:**
```python
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
# CSRF_COOKIE_SECURE = True  # Увімкнути для HTTPS в production
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
```

**Приклад використання:**
```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

---

## Контроль доступу

### Патерн: Decorator для перевірки прав

```python
# events/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def organizer_required(view_func):
    """Декоратор для перевірки, чи користувач є організатором події"""
    
    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        event = get_object_or_404(Event, pk=pk)
        if event.organizer != request.user:
            messages.error(request, "Ви не маєте прав для цієї дії")
            return redirect('event_detail', pk=pk)
        return view_func(request, pk, *args, **kwargs)
    
    return wrapper

# Використання:
@login_required
@organizer_required
def event_cancel_view(request, pk):
    # ...
```

### Рівні доступу

| Дія | Анонім | Користувач | Організатор |
|-----|--------|------------|-------------|
| Перегляд подій | ✅ | ✅ | ✅ |
| RSVP | ❌ | ✅ | ✅ |
| Створення події | ❌ | ✅ | ✅ |
| Редагування події | ❌ | ❌ | ✅ (своєї) |
| Скасування події | ❌ | ❌ | ✅ (своєї) |

---

## Захист від атак

### SQL Injection

**Захист:** Django ORM автоматично екранує всі запити

```python
# Безпечно (ORM)
Event.objects.filter(title__icontains=user_input)

# Небезпечно (raw SQL без параметрів)
Event.objects.raw(f"SELECT * FROM events WHERE title LIKE '%{user_input}%'")

# Безпечно (raw SQL з параметрами)
Event.objects.raw("SELECT * FROM events WHERE title LIKE %s", [f'%{user_input}%'])
```

### XSS (Cross-Site Scripting)

**Захист:** Django автоматично екранує всі змінні в шаблонах

```django
{# Автоматично екрановано #}
{{ event.title }}

{# Без екранування (використовувати обережно) #}
{{ event.description|safe }}

{# Безпечно з linebreaks #}
{{ event.description|linebreaksbr }}
```

### Clickjacking

**Захист:** X-Frame-Options header

```python
# settings.py
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

---

## Реалізовані патерни безпеки

Проект використовує стандартні механізми безпеки Django без додаткових патернів проектування для безпеки.

---

## 📊 Моніторинг безпеки

Проект використовує стандартні механізми логування Django.
- Створення/видалення подій
- RSVP реєстрації

---

## Checklist безпеки

### Development
- [x] CSRF токени у всіх формах
- [x] Хешування паролів (Argon2, PBKDF2 fallback)
- [x] Валідація паролів
- [x] Session management
- [x] LoginRequiredMixin для захищених views
- [x] Перевірка прав організатора

### Production (TODO)
- [ ] HTTPS (SSL/TLS)
- [ ] Secure cookies (SECURE=True)
- [ ] Rate limiting
- [ ] Security headers
- [ ] Database backups
- [ ] Monitoring та alerts

---

## Команди для безпеки

```bash
# Очистити старі сесії
python manage.py clearsessions

# Перевірити налаштування безпеки
python manage.py check --deploy

# Створити нового суперкористувача
python manage.py createsuperuser

# Змінити пароль користувача
python manage.py changepassword username
```

---

## Додаткові ресурси

- [Django Security](https://docs.djangoproject.com/en/5.2/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
