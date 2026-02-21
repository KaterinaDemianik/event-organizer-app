"""
Тести для forms.py - EventForm та ReviewForm
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from events.models import Event, Review
from events.forms import EventForm, ReviewForm


class EventFormTestCase(TestCase):
    """Тести для EventForm"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass123",
            is_staff=True
        )

    def test_event_form_valid_data(self):
        """Тест валідних даних форми"""
        now = timezone.now()
        form_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'location': 'Test Location',
            'starts_at': now + timedelta(days=1),
            'ends_at': now + timedelta(days=1, hours=2),
            'status': Event.DRAFT,
            'category': 'conference',
            'capacity': 100
        }
        
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_event_form_past_start_date(self):
        """Тест валідації дати початку в минулому"""
        now = timezone.now()
        form_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'location': 'Test Location',
            'starts_at': now - timedelta(days=1),  # Минула дата
            'ends_at': now + timedelta(days=1),
            'status': Event.DRAFT
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('starts_at', form.errors)
        self.assertIn('не може бути в минулому', str(form.errors['starts_at']))

    def test_event_form_end_before_start(self):
        """Тест валідації коли кінець раніше початку"""
        now = timezone.now()
        form_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'location': 'Test Location',
            'starts_at': now + timedelta(days=2),
            'ends_at': now + timedelta(days=1),  # Раніше початку
            'status': Event.DRAFT
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('пізніше дати початку', str(form.errors['__all__']))

    def test_event_form_negative_capacity(self):
        """Тест валідації від'ємної місткості"""
        now = timezone.now()
        form_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'location': 'Test Location',
            'starts_at': now + timedelta(days=1),
            'ends_at': now + timedelta(days=1, hours=2),
            'status': Event.DRAFT,
            'capacity': -10  # Від'ємна місткість
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('capacity', form.errors)
        # Перевіряємо що є помилка валідації для від'ємного значення
        self.assertTrue(len(form.errors['capacity']) > 0)

    def test_event_form_zero_capacity(self):
        """Тест валідації нульової місткості"""
        now = timezone.now()
        form_data = {
            'title': 'Test Event',
            'description': 'Test Description',
            'location': 'Test Location',
            'starts_at': now + timedelta(days=1),
            'ends_at': now + timedelta(days=1, hours=2),
            'status': Event.DRAFT,
            'capacity': 0  # Нульова місткість
        }
        
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('capacity', form.errors)

    def test_event_form_new_event_status_choices(self):
        """Тест обмеження статусів для нової події"""
        form = EventForm()
        
        # Для нової події доступні тільки DRAFT та PUBLISHED
        status_values = [choice[0] for choice in form.fields['status'].choices]
        self.assertIn(Event.DRAFT, status_values)
        self.assertIn(Event.PUBLISHED, status_values)
        # Не повинно бути CANCELLED або ARCHIVED
        self.assertNotIn(Event.CANCELLED, status_values)
        self.assertNotIn(Event.ARCHIVED, status_values)

    def test_event_form_existing_event_no_status_field(self):
        """Тест що для існуючої події немає поля статусу"""
        # Створюємо існуючу подію
        event = Event.objects.create(
            title="Existing Event",
            description="Description",
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        form = EventForm(instance=event)
        
        # Поле статусу має бути видалене для існуючої події
        self.assertNotIn('status', form.fields)

    def test_event_form_staff_user_organizer_field(self):
        """Тест що staff користувач має поле організатора"""
        form = EventForm(user=self.staff_user)
        
        # Staff користувач має бачити поле організатора
        self.assertIn('organizer', form.fields)
        self.assertEqual(form.fields['organizer'].initial, self.staff_user)

    def test_event_form_regular_user_no_organizer_field(self):
        """Тест що звичайний користувач не має поля організатора"""
        form = EventForm(user=self.user)
        
        # Звичайний користувач не має бачити поле організатора
        self.assertNotIn('organizer', form.fields)

    def test_event_form_field_labels(self):
        """Тест правильності лейблів полів"""
        form = EventForm()
        
        self.assertEqual(form.fields['starts_at'].label, "Дата початку")
        self.assertEqual(form.fields['ends_at'].label, "Дата закінчення")
        self.assertEqual(form.fields['capacity'].label, "Максимальна кількість учасників")
        self.assertEqual(form.fields['status'].label, "Статус події")
        self.assertEqual(form.fields['category'].label, "Категорія події")

    def test_event_form_hidden_coordinates(self):
        """Тест що координати є прихованими полями"""
        form = EventForm()
        
        self.assertFalse(form.fields['latitude'].required)
        self.assertFalse(form.fields['longitude'].required)
        # Перевіряємо що це HiddenInput віджети
        self.assertEqual(form.fields['latitude'].widget.__class__.__name__, 'HiddenInput')
        self.assertEqual(form.fields['longitude'].widget.__class__.__name__, 'HiddenInput')


class ReviewFormTestCase(TestCase):
    """Тести для ReviewForm"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )

    def test_review_form_valid_data(self):
        """Тест валідних даних форми відгуку"""
        form_data = {
            'rating': '4',
            'comment': 'Great event!'
        }
        
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_rating_choices(self):
        """Тест що рейтинг має правильні варіанти"""
        form = ReviewForm()
        
        rating_choices = [choice[0] for choice in form.fields['rating'].choices]
        expected_choices = ['1', '2', '3', '4', '5']
        
        for choice in expected_choices:
            self.assertIn(choice, rating_choices)

    def test_review_form_invalid_rating_low(self):
        """Тест валідації занадто низького рейтингу"""
        form_data = {
            'rating': '0',  # Занадто низький
            'comment': 'Bad event'
        }
        
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_review_form_invalid_rating_high(self):
        """Тест валідації занадто високого рейтингу"""
        form_data = {
            'rating': '6',  # Занадто високий
            'comment': 'Amazing event'
        }
        
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_review_form_clean_rating_conversion(self):
        """Тест конвертації рейтингу в int"""
        form_data = {
            'rating': '3',
            'comment': 'Good event'
        }
        
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Перевіряємо що clean_rating повертає int
        cleaned_rating = form.clean_rating()
        self.assertIsInstance(cleaned_rating, int)
        self.assertEqual(cleaned_rating, 3)

    def test_review_form_field_widgets(self):
        """Тест правильності віджетів полів"""
        form = ReviewForm()
        
        # Перевіряємо що comment має Textarea віджет
        self.assertEqual(form.fields['comment'].widget.__class__.__name__, 'Textarea')
        
        # Перевіряємо що rating має Select віджет
        self.assertEqual(form.fields['rating'].widget.__class__.__name__, 'Select')

    def test_review_form_field_labels(self):
        """Тест правильності лейблів полів"""
        form = ReviewForm()
        
        self.assertEqual(form.fields['rating'].label, "Рейтинг (1-5)")

    def test_review_form_meta_fields(self):
        """Тест що форма містить правильні поля"""
        form = ReviewForm()
        
        expected_fields = ["rating", "comment", "image"]
        for field in expected_fields:
            self.assertIn(field, form.fields)
