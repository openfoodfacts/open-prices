# Generated by Django 5.1 on 2024-09-12 13:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="location_count",
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]