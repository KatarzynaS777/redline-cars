from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cars", "0004_car_abs_system_car_airbags_car_body_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="image_path",
            field=models.CharField(
                blank=True,
                help_text="Sciezka w static, np. cars/models/bmw-m3.jpg",
                max_length=255,
            ),
        ),
    ]
