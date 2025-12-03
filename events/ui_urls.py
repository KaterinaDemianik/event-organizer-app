from django.urls import path
from .ui_views import (
    home_view,
    EventListView, 
    EventDetailView, 
    EventCreateView, 
    EventUpdateView, 
    CalendarView,
    rsvp_view, 
    rsvp_cancel_view,
    event_cancel_view,
    event_participants_view,
    event_review_create_view,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("events/", EventListView.as_view(), name="event_list"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
    path("events/create/", EventCreateView.as_view(), name="event-create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/edit/", EventUpdateView.as_view(), name="event-edit"),
    path("events/<int:pk>/cancel/", event_cancel_view, name="event-cancel"),
    path("events/<int:pk>/participants/", event_participants_view, name="event-participants"),
    path("events/<int:pk>/rsvp/", rsvp_view, name="event-rsvp"),
    path("events/<int:pk>/rsvp/cancel/", rsvp_cancel_view, name="event-rsvp-cancel"),
    path("events/<int:pk>/review/", event_review_create_view, name="event-review-create"),
]