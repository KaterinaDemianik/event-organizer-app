# Налаштування MySQL для Event Organizer

## 📋 Вимоги
- Python 3.13+
- MySQL 8.0+
- pip

## 🚀 Швидкий старт

### 1. Встановлення MySQL (macOS)
```bash
brew install mysql
brew services start mysql
```

### 2. Створення бази даних
```bash
mysql -u root -e "CREATE DATABASE event_organizer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. Встановлення залежностей
```bash
pip install -r requirements.txt
```

### 4. Налаштування бази даних
База даних вже налаштована в `event_organizer/settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "event_organizer",
        "USER": "root",
        "PASSWORD": "",  # Встановіть пароль якщо потрібно
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

### 5. Міграції
```bash
python manage.py migrate
```

### 6. Завантаження тестових даних
```bash
python load_test_data.py
```

### 7. Запуск сервера
```bash
python manage.py runserver
```

## 👤 Тестові облікові записи

| Користувач | Пароль | Роль |
|------------|--------|------|
| admin | admin123 | Суперкористувач |
| Katerina_demianik | password123 | Організатор |
| ivan_petrov | password123 | Учасник |

## 🗄️ Структура бази даних

### Таблиці:
- **auth_user** - Користувачі
- **events_event** - Події
- **tickets_rsvp** - Реєстрації на події

### Зв'язки:
```
User (1) ──── (N) Event (організатор)
User (N) ──── (N) Event (через RSVP)
```

## 🔧 Корисні команди

### Перевірка підключення до MySQL
```bash
mysql -u root -e "SHOW DATABASES;"
```

### Резервне копіювання
```bash
mysqldump -u root event_organizer > backup.sql
```

### Відновлення з резервної копії
```bash
mysql -u root event_organizer < backup.sql
```

### Перегляд таблиць
```bash
mysql -u root -e "USE event_organizer; SHOW TABLES;"
```

### Очищення бази даних
```bash
mysql -u root -e "DROP DATABASE event_organizer; CREATE DATABASE event_organizer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
python manage.py migrate
python load_test_data.py
```

## 📊 Переваги MySQL над SQLite

✅ **Масштабованість** - підтримка тисяч одночасних користувачів  
✅ **Продуктивність** - оптимізовані індекси та запити  
✅ **Concurrent writes** - множинні користувачі можуть писати одночасно  
✅ **Транзакції** - ACID гарантії  
✅ **Віддалений доступ** - можна підключатися з інших серверів  
✅ **Резервне копіювання** - вбудовані інструменти  
✅ **Репликація** - для високої доступності  

## 🐛 Troubleshooting

### Помилка: "Can't connect to MySQL server"
```bash
brew services restart mysql
```

### Помилка: "Access denied for user 'root'"
```bash
mysql -u root
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
FLUSH PRIVILEGES;
```

### Помилка: "Database 'event_organizer' doesn't exist"
```bash
mysql -u root -e "CREATE DATABASE event_organizer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 📝 Примітки

- PyMySQL використовується замість mysqlclient для простоти встановлення
- UTF8MB4 підтримує всі Unicode символи, включаючи емодзі
- Charset встановлений на utf8mb4 для підтримки української мови
