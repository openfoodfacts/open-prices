# Generated by Django 5.1 on 2024-09-12 14:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_product_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="proof_count",
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]