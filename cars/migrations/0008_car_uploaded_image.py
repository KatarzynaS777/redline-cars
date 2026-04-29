from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cars", "0007_car_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="uploaded_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="car_uploads/",
                verbose_name="Wlasne zdjecie",
            ),
        ),
    ]
