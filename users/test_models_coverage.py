"""
Тести для users/models.py - покриття UserProfile моделі
"""
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date

from users.models import UserProfile


class UserProfileModelTestCase(TestCase):
    """Тести для UserProfile моделі"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_user_profile_creation(self):
        """Тест створення UserProfile"""
        profile = UserProfile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1),
            city="Київ",
            phone="+380123456789"
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.birth_date, date(1990, 1, 1))
        self.assertEqual(profile.city, "Київ")
        self.assertEqual(profile.phone, "+380123456789")

    def test_user_profile_str_method(self):
        """Тест __str__ методу UserProfile"""
        profile = UserProfile.objects.create(
            user=self.user,
            city="Львів"
        )
        
        expected_str = f"Profile({self.user.id})"
        self.assertEqual(str(profile), expected_str)

    def test_user_profile_optional_fields(self):
        """Тест що опціональні поля можуть бути порожніми"""
        profile = UserProfile.objects.create(user=self.user)
        
        self.assertIsNone(profile.birth_date)
        self.assertEqual(profile.city, "")
        self.assertEqual(profile.phone, "")

    def test_user_profile_cascade_delete(self):
        """Тест що UserProfile видаляється при видаленні User"""
        profile = UserProfile.objects.create(
            user=self.user,
            city="Одеса"
        )
        
        profile_id = profile.id
        
        # Видаляємо користувача
        self.user.delete()
        
        # Перевіряємо що профіль також видалено
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())

    def test_user_profile_related_name(self):
        """Тест related_name для доступу до профілю через користувача"""
        profile = UserProfile.objects.create(
            user=self.user,
            city="Харків"
        )
        
        # Перевіряємо що можна отримати профіль через user.profile
        self.assertEqual(self.user.profile, profile)

    def test_user_profile_fields_max_length(self):
        """Тест максимальної довжини полів"""
        # Тест city max_length=100
        long_city = "A" * 100
        profile = UserProfile.objects.create(
            user=self.user,
            city=long_city
        )
        self.assertEqual(len(profile.city), 100)
        
        # Тест phone max_length=30
        long_phone = "1" * 30
        profile.phone = long_phone
        profile.save()
        self.assertEqual(len(profile.phone), 30)

    def test_user_profile_blank_fields(self):
        """Тест що поля можуть бути blank"""
        profile = UserProfile(user=self.user)
        
        # Перевіряємо що форма буде валідною з порожніми полями
        # (це тестує blank=True налаштування)
        try:
            profile.full_clean()
        except Exception:
            self.fail("UserProfile should allow blank fields")

    def test_user_profile_birth_date_null(self):
        """Тест що birth_date може бути null"""
        profile = UserProfile.objects.create(
            user=self.user,
            birth_date=None
        )
        
        self.assertIsNone(profile.birth_date)
        
        # Перевіряємо що можна зберегти з null birth_date
        profile.save()
        
        # Перезавантажуємо з БД
        profile.refresh_from_db()
        self.assertIsNone(profile.birth_date)
