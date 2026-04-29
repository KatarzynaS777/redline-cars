from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cars", "0006_favorite"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submitted_cars",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
