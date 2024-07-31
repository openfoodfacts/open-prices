from django.core.validators import ValidationError
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils import timezone

from open_prices.common import utils
from open_prices.locations import constants as location_constants


class Location(models.Model):
    CREATE_FIELDS = ["osm_id", "osm_type"]

    osm_id = models.PositiveBigIntegerField()
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

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    # proof_count = models.PositiveIntegerField(default=0, blank=True, null=True)  # noqa

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        # managed = False
        db_table = "locations"
        unique_together = ["osm_id", "osm_type"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # osm rules
        if not self.osm_id:
            validation_errors = utils.add_validation_error(
                validation_errors,
                "osm_id",
                "Should be set",
            )
        elif self.osm_id in [True, "true", "false", "none", "null"]:
            validation_errors = utils.add_validation_error(
                validation_errors,
                "osm_id",
                "Should not be a boolean or an invalid string",
            )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


@receiver(signals.post_save, sender=Location)
def location_post_create_fetch_data_from_openstreetmap(
    sender, instance, created, **kwargs
):
    if created:
        from open_prices.common import openstreetmap as common_openstreetmap

        location_openstreetmap_details = common_openstreetmap.get_location_dict(
            instance
        )
        if location_openstreetmap_details:
            for key, value in location_openstreetmap_details.items():
                setattr(instance, key, value)
            instance.save()
