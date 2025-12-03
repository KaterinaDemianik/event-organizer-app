def tab_context(request):
    """Додає поточну вкладку в контекст для навігації"""
    return {
        'tab': request.GET.get('tab', '')
    }