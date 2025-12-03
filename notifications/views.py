from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from notifications.models import Notification


@login_required
def notifications_list_view(request):
    """
    Сторінка зі списком всіх сповіщень користувача
    """
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related('event').order_by('-created_at')
    
    # Позначити всі непрочитані як прочитані при відкритті сторінки
    unread_ids = [n.id for n in notifications if not n.is_read]
    if unread_ids:
        Notification.objects.filter(id__in=unread_ids).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_notification_read(request, pk):
    """
    Позначити конкретне сповіщення як прочитане
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications_list')


@login_required
def mark_all_read(request):
    """
    Позначити всі сповіщення як прочитані
    """
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    return redirect('notifications_list')
