
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_alter_event_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("conference", "Конференція"),
                    ("webinar", "Вебінар"),
                    ("workshop", "Воркшоп"),
                    ("networking", "Нетворкінг"),
                ],
                default="",
                help_text="Тип події",
                max_length=50,
            ),
        ),
    ]