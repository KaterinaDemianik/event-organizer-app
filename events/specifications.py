"""
Specification Pattern для фільтрації подій.
Дозволяє комбінувати умови фільтрації у гнучкий спосіб.
"""
from abc import ABC, abstractmethod
from django.db.models import Q, QuerySet


class Specification(ABC):
    """Базовий клас для специфікацій фільтрації"""
    
    @abstractmethod
    def to_queryset_filter(self) -> Q:
        """Повертає Q-об'єкт для фільтрації QuerySet"""
        pass



class EventByStatusSpecification(Specification):
    """Фільтрація подій за статусом"""
    
    def __init__(self, status: str):
        self.status = status
    
    def to_queryset_filter(self) -> Q:
        return Q(status=self.status)


class EventByTitleSpecification(Specification):
    """Фільтрація подій за назвою (пошук)"""
    
    def __init__(self, query: str):
        self.query = query
    
    def to_queryset_filter(self) -> Q:
        return Q(title__icontains=self.query)


class EventByLocationSpecification(Specification):
    """Фільтрація подій за місцем"""
    
    def __init__(self, location: str):
        self.location = location
    
    def to_queryset_filter(self) -> Q:
        return Q(location__icontains=self.location)


def apply_specifications(queryset: QuerySet, *specs: Specification) -> QuerySet:
    """
    Застосовує список специфікацій до QuerySet.
    Комбінує всі специфікації через AND.
    """
    combined_q = Q()
    for spec in specs:
        if spec:
            combined_q &= spec.to_queryset_filter()
    return queryset.filter(combined_q) if combined_q else queryset