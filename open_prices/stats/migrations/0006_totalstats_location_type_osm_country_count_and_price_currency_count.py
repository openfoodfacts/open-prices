# Generated by Django 5.1.4 on 2025-02-02 16:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "stats",
            "0005_rename_price_tag_linked_to_price_count_totalstats_price_tag_status_linked_to_price_count_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="totalstats",
            name="location_type_osm_country_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="totalstats",
            name="price_currency_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
