# Приклади використання патернів

## Specification Pattern
```python
from events.specifications import PublishedEventsSpecification, apply_specifications
spec = PublishedEventsSpecification()
events = apply_specifications(Event.objects.all(), spec)
```

## Repository Pattern
```python
from events.repositories import EventRepository
repo = EventRepository()
event = repo.get_by_id(1)
published = repo.get_published()
```

## Factory Pattern
```python
from events.factories import EventFactory
conference = EventFactory.create_conference(
    title="Django Conf", organizer=user, 
    starts_at=start_date, duration_days=3
)
```

## Builder Pattern
```python
from events.builders import EventBuilder
event = (EventBuilder()
    .with_title("Конференція")
    .with_organizer(user)
    .with_capacity(500)
    .as_published()
    .build())
```

## Strategy Pattern
```python
from events.strategies import get_sort_strategy
strategy = get_sort_strategy('popularity')
sorted_qs = strategy.sort(queryset)
```
