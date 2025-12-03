"""
Proxy Pattern для управління користувацькими сесіями
"""


class SessionManager:
    """
    Proxy патерн для управління користувацькими сесіями.
    Надає зручний інтерфейс для роботи з Django session.
    """

    def __init__(self, request):
        self.session = request.session

    def set_user_preference(self, key: str, value):
        """Зберігає налаштування користувача в сесії"""
        self.session[f'pref_{key}'] = value
        self.session.modified = True

    def get_user_preference(self, key: str, default=None):
        """Отримує налаштування користувача з сесії"""
        return self.session.get(f'pref_{key}', default)

    def clear_preferences(self):
        """Очищає всі налаштування користувача"""
        keys = [k for k in self.session.keys() if k.startswith('pref_')]
        for key in keys:
            del self.session[key]
        self.session.modified = True

    def set_last_viewed_event(self, event_id: int):
        """Зберігає ID останньої переглянутої події"""
        self.session['last_viewed_event'] = event_id
        self.session.modified = True

    def get_last_viewed_event(self):
        """Отримує ID останньої переглянутої події"""
        return self.session.get('last_viewed_event')

    def add_to_history(self, event_id: int, max_items: int = 10):
        """Додає подію до історії переглядів"""
        history = self.session.get('view_history', [])
        if event_id in history:
            history.remove(event_id)
        history.insert(0, event_id)
        self.session['view_history'] = history[:max_items]
        self.session.modified = True

    def get_view_history(self):
        """Отримує історію переглядів"""
        return self.session.get('view_history', [])

    def clear_history(self):
        """Очищає історію переглядів"""
        if 'view_history' in self.session:
            del self.session['view_history']
            self.session.modified = True