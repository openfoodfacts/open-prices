import decimal

from django.core.validators import MinValueValidator, ValidationError
from django.db import models
from django.db.models import F, signals
from django.dispatch import receiver
from django.utils import timezone
from openfoodfacts.taxonomy import get_taxonomy

from open_prices.common import constants, utils
from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.products.models import Product
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import Proof
from open_prices.users.models import User


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
        "proof_id",  # extra field
    ]

    product_code = models.CharField(blank=True, null=True)
    product_name = models.CharField(blank=True, null=True)
    category_tag = models.CharField(blank=True, null=True)
    labels_tags = models.JSONField(blank=True, null=True)
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
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )
    price_is_discounted = models.BooleanField(
        default=False, blank=True, null=True
    )  # TODO: remove default=False
    price_without_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal(0))],
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
        # managed = False
        db_table = "prices"
        verbose_name = "Price"
        verbose_name_plural = "Prices"

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = dict()
        # product rules
        # - if product_code is set, then should be a valid string
        # - if product_code is set, then category_tag/labels_tags/origins_tags should not be set  # noqa
        # - if product_code is set, then price_per should not be set
        if self.product_code:
            if not isinstance(self.product_code, str):
                validation_errors = utils.add_validation_error(
                    validation_errors, "product_code", "Should be a string"
                )
            if not self.product_code.isalnum():
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "product_code",
                    "Should only contain numbers (or letters)",
                )
            if self.product_code.lower() in ["true", "false", "none", "null"]:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "product_code",
                    "Should not be a boolean or an invalid string",
                )
            if self.category_tag:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "category_tag",
                    "Should not be set if `product_code` is filled",
                )
            if self.labels_tags:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "labels_tags",
                    "Should not be set if `product_code` is filled",
                )
            if self.origins_tags:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "origins_tags",
                    "Should not be set if `product_code` is filled",
                )
            if self.price_per:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "price_per",
                    "Should not be set if `product_code` is filled",
                )
        # category_tag rules
        # - if category_tag is set, then should be a valid taxonomy string
        # - if labels_tags is set, then all labels_tags should be valid taxonomy strings  # noqa
        # - if origins_tags is set, then all origins_tags should be valid taxonomy strings  # noqa
        elif self.category_tag:
            category_taxonomy = get_taxonomy("category")
            if self.category_tag not in category_taxonomy:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "category_tag",
                    f"Invalid category tag: category '{self.category_tag}' does not exist in the taxonomy",
                )
            if self.labels_tags:
                if not isinstance(self.labels_tags, list):
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "labels_tags",
                        "Should be a list",
                    )
                else:
                    labels_taxonomy = get_taxonomy("label")
                    for label_tag in self.labels_tags:
                        if label_tag not in labels_taxonomy:
                            validation_errors = utils.add_validation_error(
                                validation_errors,
                                "labels_tags",
                                f"Invalid label tag: label '{label_tag}' does not exist in the taxonomy",
                            )
            if self.origins_tags:
                if not isinstance(self.origins_tags, list):
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "origins_tags",
                        "Should be a list",
                    )
                else:
                    origins_taxonomy = get_taxonomy("origin")
                    for origin_tag in self.origins_tags:
                        if origin_tag not in origins_taxonomy:
                            validation_errors = utils.add_validation_error(
                                validation_errors,
                                "origins_tags",
                                f"Invalid origin tag: origin '{origin_tag}' does not exist in the taxonomy",
                            )
        else:
            validation_errors = utils.add_validation_error(
                validation_errors,
                "product_code",
                "Should be set if `category_tag` is not filled",
            )
        # price rules
        # - price must be set
        # - price_is_discounted must be set if price_without_discount is set
        # - price_without_discount must be greater or equal to price
        # - price_per should be set if category_tag is set
        # - date should have the right format & not be in the future
        if self.price in [None, "true", "false", "none", "null"]:
            validation_errors = utils.add_validation_error(
                validation_errors,
                "price",
                "Should not be a boolean or an invalid string",
            )
        else:
            if self.price_without_discount:
                if not self.price_is_discounted:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "price_is_discounted",
                        "Should be set to True if `price_without_discount` is filled",
                    )
                if (
                    utils.is_float(self.price)
                    and utils.is_float(self.price_without_discount)
                    and (self.price_without_discount <= self.price)
                ):
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "price_without_discount",
                        "Should be greater than `price`",
                    )
        if self.product_code:
            if self.price_per:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "price_per",
                    "Should not be set if `product_code` is filled",
                )
        if self.category_tag:
            if not self.price_per:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "price_per",
                    "Should be set if `category_tag` is filled",
                )
        if self.date:
            if type(self.date) is str:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "date",
                    "Parsing error. Expected format: YYYY-MM-DD",
                )
            elif self.date > timezone.now().date():
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "date",
                    "Should not be in the future",
                )
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
        # proof rules
        # - proof must exist and belong to the price owner
        # - some proof fields should be the same as the price fields
        if self.proof_id:
            from open_prices.proofs.models import Proof

            try:
                proof = Proof.objects.get(id=self.proof_id)
            except Proof.DoesNotExist:
                validation_errors = utils.add_validation_error(
                    validation_errors,
                    "proof",
                    "Proof not found",
                )

            if proof:
                if proof.owner != self.owner:
                    validation_errors = utils.add_validation_error(
                        validation_errors,
                        "proof",
                        "Proof does not belong to the current user",
                    )
                if proof.type in [
                    proof_constants.TYPE_RECEIPT,
                    proof_constants.TYPE_PRICE_TAG,
                ]:
                    for PROOF_FIELD in Proof.DUPLICATE_PRICE_FIELDS:
                        proof_field_value = getattr(self.proof, PROOF_FIELD)
                        if proof_field_value:
                            price_field_value = getattr(self, PROOF_FIELD)
                            if str(proof_field_value) != str(price_field_value):
                                validation_errors = utils.add_validation_error(
                                    validation_errors,
                                    "proof",
                                    f"Proof {PROOF_FIELD} ({proof_field_value}) does not match the price {PROOF_FIELD} ({price_field_value})",
                                )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def get_or_create_product(self):
        if self.product_code:
            from open_prices.products.models import Product

            product, created = Product.objects.get_or_create(code=self.product_code)
            self.product = product

    def get_or_create_location(self):
        if self.location_osm_id and self.location_osm_type:
            from open_prices.locations.models import Location

            location, created = Location.objects.get_or_create(
                osm_id=self.location_osm_id, osm_type=self.location_osm_type
            )
            self.location = location

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.id:  # new price
            # self.set_proof()  # should already exist
            self.get_or_create_product()
            self.get_or_create_location()
        super().save(*args, **kwargs)


@receiver(signals.post_save, sender=Price)
def price_post_create_increment_counts(sender, instance, created, **kwargs):
    if instance.owner:
        User.objects.filter(user_id=instance.owner).update(
            price_count=F("price_count") + 1
        )
    if instance.proof:
        Proof.objects.filter(id=instance.proof.id).update(
            price_count=F("price_count") + 1
        )
    if instance.product:
        Product.objects.filter(id=instance.product.id).update(
            price_count=F("price_count") + 1
        )
    if instance.location:
        Location.objects.filter(id=instance.location.id).update(
            price_count=F("price_count") + 1
        )


@receiver(signals.post_delete, sender=Price)
def price_post_delete_decrement_counts(sender, instance, **kwargs):
    if instance.owner:
        User.objects.filter(user_id=instance.owner).update(
            price_count=F("price_count") - 1
        )
    if instance.proof:
        Proof.objects.filter(id=instance.proof.id).update(
            price_count=F("price_count") - 1
        )
    if instance.product:
        Product.objects.filter(id=instance.product.id).update(
            price_count=F("price_count") - 1
        )
    if instance.location:
        Location.objects.filter(id=instance.location.id).update(
            price_count=F("price_count") - 1
        )
