# Generated by Django 5.1.4 on 2024-12-23 10:49

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("stats", "0004_totalstats_price_tag_count_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="totalstats",
            old_name="price_tag_status_linked_to_price_count",
            new_name="price_tag_status_linked_to_price_count",
        ),
        migrations.RenameField(
            model_name="totalstats",
            old_name="price_tag_status_unknown_count",
            new_name="price_tag_status_unknown_count",
        ),
    ]
