
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0007_event_latitude_event_longitude"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="capacity",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Залиште порожнім, якщо без обмежень.",
                null=True,
            ),
        ),
    ]