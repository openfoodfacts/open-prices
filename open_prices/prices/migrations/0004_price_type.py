# Generated by Django 5.1 on 2024-11-26 09:48

from django.db import migrations, models


def set_price_type_category(apps, schema_editor):
    Price = apps.get_model("prices", "Price")
    # Price.objects.filter(product_code__isnull=False).update(type="PRODUCT")
    Price.objects.filter(category_tag__isnull=False).update(type="CATEGORY")


class Migration(migrations.Migration):
    dependencies = [
        ("prices", "0003_price_receipt_quantity"),
    ]

    operations = [
        migrations.AddField(
            model_name="price",
            name="type",
            field=models.CharField(
                choices=[("PRODUCT", "PRODUCT"), ("CATEGORY", "CATEGORY")],
                default="PRODUCT",  # used only for the migration
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_price_type_category),
    ]