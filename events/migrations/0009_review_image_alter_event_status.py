
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0008_event_capacity"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Необов'язково: додайте зображення до свого відгуку (скрін, фото з події тощо).",
                null=True,
                upload_to="review_photos/",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Чернетка"),
                    ("published", "Опубліковано"),
                    ("cancelled", "Скасовано"),
                    ("archived", "Архів"),
                ],
                default="draft",
                max_length=20,
            ),
        ),
    ]