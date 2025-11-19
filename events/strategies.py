from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from django.db.models import QuerySet


class SortStrategy(ABC):
    """Базова стратегія сортування подій"""

    slug: str = "date"
    label: str = "За датою"

    @abstractmethod
    def sort(self, queryset: QuerySet) -> QuerySet:
        raise NotImplementedError


class SortByDateStrategy(SortStrategy):
    slug = "date"
    label = "Найближчі зверху"

    def sort(self, queryset: QuerySet) -> QuerySet:
        return queryset.order_by("-starts_at")


class SortByPopularityStrategy(SortStrategy):
    slug = "popularity"
    label = "Найпопулярніші"

    def sort(self, queryset: QuerySet) -> QuerySet:
        # rsvp_count вже наявний як анотація у базовому queryset
        return queryset.order_by("-rsvp_count", "-starts_at")


class SortByAlphabetStrategy(SortStrategy):
    slug = "alphabet"
    label = "За абеткою"

    def sort(self, queryset: QuerySet) -> QuerySet:
        return queryset.order_by("title")


AVAILABLE_STRATEGIES: List[SortStrategy] = [
    SortByDateStrategy(),
    SortByPopularityStrategy(),
    SortByAlphabetStrategy(),
]

STRATEGIES: Dict[str, SortStrategy] = {s.slug: s for s in AVAILABLE_STRATEGIES}


def get_sort_strategy(slug: str) -> SortStrategy:
    """Повертає стратегію сортування за ключем"""

    return STRATEGIES.get(slug, STRATEGIES["date"])


def get_sort_choices() -> List[SortStrategy]:
    """Повертає відсортований список стратегій для UI"""

    return AVAILABLE_STRATEGIES
