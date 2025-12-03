
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_event_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="category",
            field=models.CharField(
                blank=True,
                help_text="Тип події (вільний текст, наприклад: конференція, вебінар, воркшоп)",
                max_length=100,
            ),
        ),
    ]