"""
Specification Pattern для фільтрації подій.
Дозволяє комбінувати умови фільтрації у гнучкий спосіб.
"""
from abc import ABC, abstractmethod
from django.db.models import Q, QuerySet
from typing import Optional
from datetime import datetime


class Specification(ABC):
    """Базовий клас для специфікацій фільтрації"""
    
    @abstractmethod
    def is_satisfied_by(self, obj) -> bool:
        """Перевіряє, чи задовольняє об'єкт специфікації"""
        pass
    
    @abstractmethod
    def to_queryset_filter(self) -> Q:
        """Повертає Q-об'єкт для фільтрації QuerySet"""
        pass
    
    def __and__(self, other: 'Specification') -> 'AndSpecification':
        return AndSpecification(self, other)
    
    def __or__(self, other: 'Specification') -> 'OrSpecification':
        return OrSpecification(self, other)
    
    def __invert__(self) -> 'NotSpecification':
        return NotSpecification(self)


class AndSpecification(Specification):
    """Логічне AND для двох специфікацій"""
    
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, obj) -> bool:
        return self.left.is_satisfied_by(obj) and self.right.is_satisfied_by(obj)
    
    def to_queryset_filter(self) -> Q:
        return self.left.to_queryset_filter() & self.right.to_queryset_filter()


class OrSpecification(Specification):
    """Логічне OR для двох специфікацій"""
    
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, obj) -> bool:
        return self.left.is_satisfied_by(obj) or self.right.is_satisfied_by(obj)
    
    def to_queryset_filter(self) -> Q:
        return self.left.to_queryset_filter() | self.right.to_queryset_filter()


class NotSpecification(Specification):
    """Логічне NOT для специфікації"""
    
    def __init__(self, spec: Specification):
        self.spec = spec
    
    def is_satisfied_by(self, obj) -> bool:
        return not self.spec.is_satisfied_by(obj)
    
    def to_queryset_filter(self) -> Q:
        return ~self.spec.to_queryset_filter()



class EventByStatusSpecification(Specification):
    """Фільтрація подій за статусом"""
    
    def __init__(self, status: str):
        self.status = status
    
    def is_satisfied_by(self, event) -> bool:
        return event.status == self.status
    
    def to_queryset_filter(self) -> Q:
        return Q(status=self.status)


class EventByTitleSpecification(Specification):
    """Фільтрація подій за назвою (пошук)"""
    
    def __init__(self, query: str):
        self.query = query
    
    def is_satisfied_by(self, event) -> bool:
        return self.query.lower() in event.title.lower()
    
    def to_queryset_filter(self) -> Q:
        return Q(title__icontains=self.query)


class EventByLocationSpecification(Specification):
    """Фільтрація подій за місцем"""
    
    def __init__(self, location: str):
        self.location = location
    
    def is_satisfied_by(self, event) -> bool:
        return self.location.lower() in event.location.lower()
    
    def to_queryset_filter(self) -> Q:
        return Q(location__icontains=self.location)


class EventByDateRangeSpecification(Specification):
    """Фільтрація подій за діапазоном дат"""
    
    def __init__(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        self.start_date = start_date
        self.end_date = end_date
    
    def is_satisfied_by(self, event) -> bool:
        if self.start_date and event.starts_at < self.start_date:
            return False
        if self.end_date and event.starts_at > self.end_date:
            return False
        return True
    
    def to_queryset_filter(self) -> Q:
        q = Q()
        if self.start_date:
            q &= Q(starts_at__gte=self.start_date)
        if self.end_date:
            q &= Q(starts_at__lte=self.end_date)
        return q


class PublishedEventsSpecification(Specification):
    """Фільтрація тільки опублікованих подій"""
    
    def is_satisfied_by(self, event) -> bool:
        return event.status == 'published'
    
    def to_queryset_filter(self) -> Q:
        return Q(status='published')


class UpcomingEventsSpecification(Specification):
    """Фільтрація майбутніх подій"""
    
    def __init__(self, from_date: Optional[datetime] = None):
        self.from_date = from_date or datetime.now()
    
    def is_satisfied_by(self, event) -> bool:
        return event.starts_at >= self.from_date
    
    def to_queryset_filter(self) -> Q:
        return Q(starts_at__gte=self.from_date)


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