from django.db import models
from django.utils import timezone

from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.prices import constants as price_constants


class Price(models.Model):
    product_code = models.CharField(blank=True, null=True)
    category_tag = models.CharField(blank=True, null=True)
    labels_tags = models.JSONField(blank=True, null=True)
    product_name = models.CharField(blank=True, null=True)
    origins_tags = models.JSONField(blank=True, null=True)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="prices",
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_is_discounted = models.BooleanField(blank=True, null=True)
    price_without_discount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    price_per = models.CharField(
        max_length=10,
        choices=price_constants.PRICE_PER_CHOICES,
        blank=True,
        null=True,
    )
    currency = models.CharField(
        max_length=3, choices=constants.CURRENCY_CHOICES, blank=True, null=True
    )

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
        related_name="prices",
    )

    date = models.DateField(blank=True, null=True)

    proof = models.ForeignKey(
        "proofs.Proof",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="prices",
    )

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "prices"
        verbose_name = "Price"
        verbose_name_plural = "Prices"
