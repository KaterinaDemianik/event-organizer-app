"""
Тести для Strategy Pattern - стратегії сортування подій
"""
from django.test import TestCase
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from events.models import Event
from events.strategies import (
    SortByDateStrategy,
    SortByPopularityStrategy,
    SortByAlphabetStrategy,
    SortByEventDateStrategy,
    SortByRsvpCountStrategy,
    get_sort_strategy,
    STRATEGIES,
    AVAILABLE_STRATEGIES
)
from tickets.models import RSVP
from django.contrib.auth.models import User


class StrategyPatternTestCase(TestCase):
    """Тести для Strategy Pattern сортування"""

    def setUp(self):
        """Створюємо тестові дані"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        now = timezone.now()
        
        # Створюємо події з різними датами та назвами
        self.event1 = Event.objects.create(
            title="Zebra Event",
            description="Last in alphabet",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        self.event2 = Event.objects.create(
            title="Alpha Event", 
            description="First in alphabet",
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        self.event3 = Event.objects.create(
            title="Beta Event",
            description="Middle in alphabet",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
            organizer=self.user,
            status=Event.PUBLISHED
        )
        
        # Створюємо RSVP для тестування популярності
        for i in range(3):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="pass123"
            )
            RSVP.objects.create(
                user=user,
                event=self.event2,  # Alpha Event буде найпопулярнішим
                status="going"
            )
        
        # Одна реєстрація для Beta Event
        user4 = User.objects.create_user(
            username="user4",
            email="user4@example.com", 
            password="pass123"
        )
        RSVP.objects.create(
            user=user4,
            event=self.event3,
            status="going"
        )

    def get_annotated_queryset(self):
        """Повертає queryset з анотацією rsvp_count"""
        return Event.objects.annotate(
            rsvp_count=Count('rsvps', filter=Q(rsvps__status="going"), distinct=True)
        )

    def test_sort_by_date_strategy(self):
        """Тест стратегії сортування за датою (найближчі зверху)"""
        strategy = SortByDateStrategy()
        
        self.assertEqual(strategy.slug, "date")
        self.assertEqual(strategy.label, "Найближчі зверху")
        
        queryset = self.get_annotated_queryset()
        sorted_events = list(strategy.sort(queryset))
        
        # Має бути відсортовано за -starts_at (найближчі зверху)
        self.assertEqual(sorted_events[0], self.event2)  # +3 дні
        self.assertEqual(sorted_events[1], self.event3)  # +2 дні  
        self.assertEqual(sorted_events[2], self.event1)  # +1 день

    def test_sort_by_popularity_strategy(self):
        """Тест стратегії сортування за популярністю"""
        strategy = SortByPopularityStrategy()
        
        self.assertEqual(strategy.slug, "popular")
        self.assertEqual(strategy.label, "Найпопулярніші")
        
        queryset = self.get_annotated_queryset()
        sorted_events = list(strategy.sort(queryset))
        
        # Alpha Event має 3 RSVP, Beta Event має 1, Zebra Event має 0
        self.assertEqual(sorted_events[0], self.event2)  # Alpha - 3 RSVP
        self.assertEqual(sorted_events[1], self.event3)  # Beta - 1 RSVP
        self.assertEqual(sorted_events[2], self.event1)  # Zebra - 0 RSVP

    def test_sort_by_alphabet_strategy(self):
        """Тест стратегії сортування за абеткою"""
        strategy = SortByAlphabetStrategy()
        
        self.assertEqual(strategy.slug, "alphabet")
        self.assertEqual(strategy.label, "За абеткою")
        
        queryset = self.get_annotated_queryset()
        sorted_events = list(strategy.sort(queryset))
        
        # Має бути відсортовано за title
        self.assertEqual(sorted_events[0], self.event2)  # Alpha Event
        self.assertEqual(sorted_events[1], self.event3)  # Beta Event
        self.assertEqual(sorted_events[2], self.event1)  # Zebra Event

    def test_sort_by_event_date_strategy(self):
        """Тест стратегії сортування за датою події (найраніші зверху)"""
        strategy = SortByEventDateStrategy()
        
        self.assertEqual(strategy.slug, "event_date")
        self.assertEqual(strategy.label, "За датою події")
        
        queryset = self.get_annotated_queryset()
        sorted_events = list(strategy.sort(queryset))
        
        # Має бути відсортовано за starts_at (найраніші зверху)
        self.assertEqual(sorted_events[0], self.event1)  # +1 день
        self.assertEqual(sorted_events[1], self.event3)  # +2 дні
        self.assertEqual(sorted_events[2], self.event2)  # +3 дні

    def test_sort_by_rsvp_count_strategy(self):
        """Тест стратегії сортування за кількістю учасників"""
        strategy = SortByRsvpCountStrategy()
        
        self.assertEqual(strategy.slug, "rsvp_count")
        self.assertEqual(strategy.label, "За кількістю учасників")
        
        queryset = self.get_annotated_queryset()
        sorted_events = list(strategy.sort(queryset))
        
        # Має бути відсортовано за -rsvp_count
        self.assertEqual(sorted_events[0], self.event2)  # 3 RSVP
        self.assertEqual(sorted_events[1], self.event3)  # 1 RSVP
        self.assertEqual(sorted_events[2], self.event1)  # 0 RSVP

    def test_get_sort_strategy_function(self):
        """Тест функції get_sort_strategy"""
        # Тест існуючих стратегій
        date_strategy = get_sort_strategy("date")
        self.assertIsInstance(date_strategy, SortByDateStrategy)
        
        popular_strategy = get_sort_strategy("popular")
        self.assertIsInstance(popular_strategy, SortByPopularityStrategy)
        
        alphabet_strategy = get_sort_strategy("alphabet")
        self.assertIsInstance(alphabet_strategy, SortByAlphabetStrategy)
        
        # Тест неіснуючої стратегії (має повернути default "date")
        default_strategy = get_sort_strategy("nonexistent")
        self.assertIsInstance(default_strategy, SortByDateStrategy)
        
        # Тест порожнього slug
        empty_strategy = get_sort_strategy("")
        self.assertIsInstance(empty_strategy, SortByDateStrategy)

    def test_strategies_dict_completeness(self):
        """Тест що всі стратегії є в STRATEGIES dict"""
        self.assertIn("date", STRATEGIES)
        self.assertIn("popular", STRATEGIES)
        self.assertIn("alphabet", STRATEGIES)
        self.assertIn("event_date", STRATEGIES)
        self.assertIn("rsvp_count", STRATEGIES)
        
        # Перевіряємо що кількість стратегій відповідає
        self.assertEqual(len(STRATEGIES), len(AVAILABLE_STRATEGIES))

    def test_available_strategies_list(self):
        """Тест що AVAILABLE_STRATEGIES містить всі стратегії"""
        self.assertEqual(len(AVAILABLE_STRATEGIES), 5)
        
        # Перевіряємо типи
        strategy_types = [type(s) for s in AVAILABLE_STRATEGIES]
        expected_types = [
            SortByDateStrategy,
            SortByPopularityStrategy, 
            SortByAlphabetStrategy,
            SortByEventDateStrategy,
            SortByRsvpCountStrategy
        ]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, strategy_types)

    def test_base_strategy_abstract_method(self):
        """Тест що базова стратегія є абстрактною"""
        from events.strategies import SortStrategy
        
        # Не можна створити екземпляр абстрактного класу
        with self.assertRaises(TypeError):
            SortStrategy()
