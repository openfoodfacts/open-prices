from django.db import models
from django.utils import timezone

from open_prices.locations import constants as location_constants


class Location(models.Model):
    osm_id = models.BigIntegerField(blank=True, null=True)
    osm_type = models.CharField(
        max_length=10, choices=location_constants.OSM_TYPE_CHOICES
    )

    osm_name = models.CharField(blank=True, null=True)
    osm_display_name = models.CharField(blank=True, null=True)
    osm_tag_key = models.CharField(blank=True, null=True)
    osm_tag_value = models.CharField(blank=True, null=True)
    osm_address_postcode = models.CharField(blank=True, null=True)
    osm_address_city = models.CharField(blank=True, null=True)
    osm_address_country = models.CharField(blank=True, null=True)
    osm_address_country_code = models.CharField(blank=True, null=True)
    osm_lat = models.DecimalField(
        max_digits=11, decimal_places=7, blank=True, null=True
    )
    osm_lon = models.DecimalField(
        max_digits=11, decimal_places=7, blank=True, null=True
    )

    price_count = models.IntegerField()

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "locations"
        verbose_name = "Location"
        verbose_name_plural = "Locations"
