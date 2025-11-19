from django.urls import path
from .ui_views import (
    EventListView, 
    EventDetailView, 
    EventCreateView, 
    EventUpdateView, 
    rsvp_view, 
    rsvp_cancel_view,
    event_cancel_view
)

urlpatterns = [
    path("", EventListView.as_view(), name="home"),
    path("events/create/", EventCreateView.as_view(), name="event-create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/edit/", EventUpdateView.as_view(), name="event-edit"),
    path("events/<int:pk>/cancel/", event_cancel_view, name="event-cancel"),
    path("events/<int:pk>/rsvp/", rsvp_view, name="event-rsvp"),
    path("events/<int:pk>/rsvp/cancel/", rsvp_cancel_view, name="event-rsvp-cancel"),
]
