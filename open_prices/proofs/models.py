from django.db import models
from django.utils import timezone

from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.proofs import constants as proof_constants


class Proof(models.Model):
    file_path = models.CharField()
    mimetype = models.CharField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=proof_constants.TYPE_CHOICES)

    location_osm_id = models.BigIntegerField(blank=True, null=True)
    location_osm_type = models.CharField(
        max_length=10, choices=location_constants.OSM_TYPE_CHOICES, blank=True, null=True
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

    price_count = models.IntegerField()

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "proofs"
        verbose_name = "Proof"
        verbose_name_plural = "Proofs"
