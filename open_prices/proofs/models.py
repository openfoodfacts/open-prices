from django.core.validators import ValidationError
from django.db import models
from django.utils import timezone

from open_prices.common import constants, utils
from open_prices.locations import constants as location_constants
from open_prices.proofs import constants as proof_constants


class Proof(models.Model):
    FILE_FIELDS = ["file_path", "mimetype"]
    UPDATE_FIELDS = ["type", "currency", "date"]
    CREATE_FIELDS = UPDATE_FIELDS + ["location_osm_id", "location_osm_type"]
    DUPLICATE_PRICE_FIELDS = [
        "location_osm_id",
        "location_osm_type",
        "date",
        "currency",
    ]  # "owner"

    file_path = models.CharField()
    mimetype = models.CharField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=proof_constants.TYPE_CHOICES)

    location_osm_id = models.PositiveBigIntegerField(blank=True, null=True)
    location_osm_type = models.CharField(
        max_length=10,
        choices=location_constants.OSM_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="proofs",
    )
    date = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=3, choices=constants.CURRENCY_CHOICES, blank=True, null=True
    )

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        # managed = False
        db_table = "proofs"
        verbose_name = "Proof"
        verbose_name_plural = "Proofs"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # location rules
        # - location_osm_id should be set if location_osm_type is set
        # - location_osm_type should be set if location_osm_id is set
        if self.location_osm_id:
            if not self.location_osm_type:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "location_osm_type",
                    "Should be set if `location_osm_id` is filled",
                )
        if self.location_osm_type:
            if not self.location_osm_id:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "location_osm_id",
                    "Should be set if `location_osm_type` is filled",
                )
            elif self.location_osm_id in [True, "true", "false", "none", "null"]:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "location_osm_id",
                    "Should not be a boolean or an invalid string",
                )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def set_location(self):
        if self.location_osm_id and self.location_osm_type:
            from open_prices.locations.models import Location

            location, created = Location.objects.get_or_create(
                osm_id=self.location_osm_id,
                osm_type=self.location_osm_type,
                # defaults={"proof_count": 1},
            )
            self.location = location

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.id:
            self.set_location()
        super().save(*args, **kwargs)
