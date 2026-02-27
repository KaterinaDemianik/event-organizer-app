from rest_framework import serializers
from .models import Event
from .states import EventStateManager


class EventSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для моделі Event з валідацією переходів статусів.
    
    Використовує State Pattern через EventStateManager для забезпечення
    коректних переходів між станами події (draft -> published -> cancelled/archived).
    """
    rsvp_count = serializers.IntegerField(read_only=True, help_text="Кількість підтверджень участі")
    
    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "location",
            "starts_at",
            "ends_at",
            "status",
            "organizer",
            "rsvp_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "organizer", "rsvp_count"]

    def validate_status(self, value):
        """
        Валідація зміни статусу події через State Pattern.
        
        При оновленні події перевіряє, чи дозволений перехід з поточного
        статусу до нового згідно з правилами EventStateManager.
        
        Raises:
            serializers.ValidationError: Якщо перехід статусу неможливий
        """
        if self.instance is None:
            return value
        
        current_status = self.instance.status
        if current_status == value:
            return value
        
        is_valid, error_message = EventStateManager.validate_transition(
            self.instance, value
        )
        
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        return value

    def validate(self, attrs):
        """
        Загальна валідація даних події.
        
        Перевіряє бізнес-правила для переходів статусів та інші обмеження.
        """
        attrs = super().validate(attrs)
        
        if self.instance and 'status' in attrs:
            new_status = attrs['status']
            current_status = self.instance.status
            
            if new_status != current_status:
                if not EventStateManager.can_transition(current_status, new_status):
                    raise serializers.ValidationError({
                        'status': f"Перехід з '{current_status}' до '{new_status}' заборонений. "
                                  f"Дозволені переходи: {EventStateManager.get_state(current_status).get_allowed_transitions()}"
                    })
        
        return attrs