from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list_view, name='notifications_list'),
    path('<int:pk>/read/', views.mark_notification_read, name='notification_mark_read'),
    path('mark-all-read/', views.mark_all_read, name='notifications_mark_all_read'),
]