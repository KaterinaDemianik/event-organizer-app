
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0002_alter_event_organizer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "draft"),
                    ("published", "published"),
                    ("cancelled", "cancelled"),
                    ("archived", "archived"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
    ]