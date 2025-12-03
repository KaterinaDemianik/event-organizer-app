
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="organizer",
            field=models.ForeignKey(
                help_text="Користувач, який створив подію",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organized_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]