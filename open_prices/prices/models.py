from django.core.validators import MinValueValidator, ValidationError
from django.db import models
from django.utils import timezone

from open_prices.common import constants, utils
from open_prices.locations import constants as location_constants
from open_prices.prices import constants as price_constants


class Price(models.Model):
    UPDATE_FIELDS = [
        "price",
        "price_is_discounted",
        "price_without_discount",
        "price_per",
        "currency",
        "date",
    ]
    CREATE_FIELDS = UPDATE_FIELDS + [
        "product_code",
        "product_name",
        "category_tag",
        "labels_tags",
        "origins_tags",
        "location_osm_id",
        "location_osm_type",
        "proof_id",
    ]

    product_code = models.CharField(blank=True, null=True, db_index=True)
    product_name = models.CharField(blank=True, null=True)
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

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )
    price_is_discounted = models.BooleanField(
        default=False, blank=True, null=True
    )  # TODO: remove default=False
    price_without_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
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

    location_osm_id = models.PositiveBigIntegerField(
        blank=True, null=True, db_index=True
    )
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
        # managed = False
        db_table = "prices"
        verbose_name = "Price"
        verbose_name_plural = "Prices"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # price rules
        # - price_is_discounted must be set if price_without_discount is set
        # - price_without_discount must be greater or equal to price
        if self.price_without_discount:
            if not self.price_is_discounted:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "price_is_discounted",
                    "Should be set to True if `price_without_discount` is filled",
                )
            if (
                self.price
                and utils.is_float(self.price)
                and utils.is_float(self.price_without_discount)
                and (self.price_without_discount <= self.price)
            ):
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "price_without_discount",
                    "Should be greater than `price`",
                )
        # proof rules
        # - proof must belong to the price owner
        if self.proof:
            if self.proof.owner != self.owner:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "proof",
                    "Proof does not belong to the current user",
                )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
