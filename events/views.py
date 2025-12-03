from django.shortcuts import render
from django.db.models import Count
from rest_framework import viewsets, permissions, decorators, response, status
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from .models import Event
from .serializers import EventSerializer
from .specifications import (
    EventByStatusSpecification,
    EventByTitleSpecification,
    EventByLocationSpecification,
    apply_specifications,
)
from tickets.models import RSVP
from tickets.serializers import RSVPSerializer


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    pass


class EventPagination(PageNumberPagination):
    """Пагінація для API подій"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class EventFilter(filters.FilterSet):
    """Фільтри для API подій"""
    q = filters.CharFilter(field_name='title', lookup_expr='icontains', label='Пошук за назвою')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains', label='Місце')
    status = filters.ChoiceFilter(choices=Event.STATUS_CHOICES, label='Статус')
    starts_after = filters.DateTimeFilter(field_name='starts_at', lookup_expr='gte', label='Починається після')
    starts_before = filters.DateTimeFilter(field_name='starts_at', lookup_expr='lte', label='Починається до')
    
    class Meta:
        model = Event
        fields = ['q', 'location', 'status', 'starts_after', 'starts_before']


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = EventPagination
    filterset_class = EventFilter
    
    def get_queryset(self):
        """Додаємо анотацію з кількістю RSVP до кожної події"""
        from django.db.models import Q
        return Event.objects.annotate(rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'), distinct=True)).order_by("-starts_at")

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def rsvp(self, request, pk=None):
        event = self.get_object()
        rsvp, created = RSVP.objects.get_or_create(user=request.user, event=event)
        ser = RSVPSerializer(rsvp)
        return response.Response(ser.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)