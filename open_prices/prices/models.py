import decimal

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, ValidationError
from django.db import models
from django.db.models import Avg, Case, Count, F, Max, Min, Q, Value, When, signals
from django.db.models.functions import Cast, ExtractYear
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task
from openfoodfacts.barcode import normalize_barcode
from simple_history.models import HistoricalRecords

from open_prices.challenges.models import Challenge

# Import custom lookups so that they are registered
from open_prices.common import (
    constants,
    history,
    lookups,  # noqa: F401
    utils,
)
from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.prices import validators as price_validators
from open_prices.products.models import Product
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import Proof
from open_prices.users.models import User


class PriceQuerySet(models.QuerySet):
    def has_discount(self):
        return self.filter(price_is_discounted=True)

    def exclude_discounted(self):
        return self.filter(price_is_discounted=False)

    def has_type_product(self):
        return self.filter(type=price_constants.TYPE_PRODUCT)

    def has_type_category(self):
        return self.filter(type=price_constants.TYPE_CATEGORY)

    def has_kind_community(self):
        return self.prefetch_related("proof").exclude(proof__owner_consumption=True)

    def has_kind_consumption(self):
        return self.prefetch_related("proof").filter(
            proof__type__in=proof_constants.TYPE_GROUP_CONSUMPTION_LIST,
            proof__owner_consumption=True,
        )

    def has_product_name(self):
        return self.filter(product_name__isnull=False).exclude(product_name="")

    def with_extra_fields(self):
        return self.annotate(
            date_year_annotated=ExtractYear("date"),
            source_annotated=Case(
                When(
                    source__contains="Open Prices Web App",
                    then=Value(constants.SOURCE_WEB),
                ),
                When(
                    source__contains="Smoothie",
                    then=Value(constants.SOURCE_MOBILE),
                ),
                When(source__contains="API", then=Value(constants.SOURCE_API)),
                default=Value(constants.SOURCE_OTHER),
                output_field=models.CharField(),
            ),
        )

    def calculate_min(self):
        return self.aggregate(Min("price"))["price__min"]

    def calculate_max(self):
        return self.aggregate(Max("price"))["price__max"]

    def calculate_avg(self):
        return self.aggregate(
            price__avg=Cast(
                Avg("price"),
                output_field=models.DecimalField(max_digits=10, decimal_places=2),
            )
        )["price__avg"]

    def calculate_stats(self):
        return self.aggregate(
            price__count=Count("pk"),
            price__min=Min("price"),
            price__max=Max("price"),
            price__avg=Cast(
                Avg("price"),
                output_field=models.DecimalField(max_digits=10, decimal_places=2),
            ),
        )

    def has_tag(self, tag: str):
        return self.filter(tags__contains=[tag])

    def in_challenge(self, challenge: Challenge):
        queryset = self.select_related("product").filter(
            created__gte=challenge.start_date_with_time,
            created__lte=challenge.end_date_with_time,
        )
        if challenge.categories:
            queryset = queryset.filter(
                Q(
                    type=price_constants.TYPE_CATEGORY,
                    category_tag__in=challenge.categories,
                )
                | Q(
                    type=price_constants.TYPE_PRODUCT,
                    product__categories_tags__overlap=challenge.categories,
                )
            )
        if challenge.locations.exists():
            queryset = queryset.filter(location_id__in=challenge.location_id_list())
        return queryset


class Price(models.Model):
    TYPE_PRODUCT_FIELDS = ["product_code"]
    TYPE_CATEGORY_FIELDS = ["category_tag", "labels_tags", "origins_tags"]
    UPDATE_FIELDS = [
        "product_code",
        # "product_name",
        "category_tag",
        "labels_tags",
        "origins_tags",
        "price",
        "price_is_discounted",
        "price_without_discount",
        "discount_type",
        "price_per",
        "currency",
        "date",
        "receipt_quantity",
        "owner_comment",
    ]
    CREATE_FIELDS = UPDATE_FIELDS + [
        "type",  # optional in the serializer
        "product_code",
        "product_name",
        "category_tag",
        "labels_tags",
        "origins_tags",
        "location_osm_id",
        "location_osm_type",
        "location_id",  # extra field (optional)
        "proof_id",  # extra field
    ]
    DUPLICATE_LOCATION_FIELDS = [
        "location_osm_id",
        "location_osm_type",
    ]
    DUPLICATE_PROOF_FIELDS = [
        # "location_id",
        "location_osm_id",
        "location_osm_type",
        "date",
        "currency",
    ]  # "owner"

    type = models.CharField(max_length=20, choices=price_constants.TYPE_CHOICES)

    product_code = models.CharField(blank=True, null=True)
    product_name = models.CharField(blank=True, null=True)
    category_tag = models.CharField(blank=True, null=True)
    labels_tags = ArrayField(base_field=models.CharField(), blank=True, null=True)
    origins_tags = ArrayField(base_field=models.CharField(), blank=True, null=True)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="prices",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )
    price_is_discounted = models.BooleanField(default=False)
    price_without_discount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )
    discount_type = models.CharField(
        max_length=20,
        choices=price_constants.DISCOUNT_TYPE_CHOICES,
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

    receipt_quantity = models.DecimalField(
        verbose_name="Receipt's price quantity (user input)",
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(decimal.Decimal(0))],
        blank=True,
        null=True,
    )

    owner_comment = models.TextField(blank=True, null=True)

    owner = models.CharField(blank=True, null=True)
    source = models.CharField(blank=True, null=True)

    tags = ArrayField(base_field=models.CharField(), blank=True, default=list)
    flags = GenericRelation("moderation.Flag", related_query_name="price")

    # If this price is a duplicate of another price, we store the reference
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="duplicates",
    )

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(
        get_user=history.get_history_user_from_request,
        history_user_id_field=models.CharField(null=True),
        history_user_getter=history.history_user_getter,
        history_user_setter=history.history_user_setter,
        # cascade_delete_history=False,  # default
    )

    objects = models.Manager.from_queryset(PriceQuerySet)()

    class Meta:
        db_table = "prices"
        verbose_name = "Price"
        verbose_name_plural = "Prices"

    def normalize_product_code(self):
        """
        Normalize the product_code (remove leading zeros, pad to 8 or 13 digits).  # noqa
        """
        if (
            self.product_code
            and isinstance(self.product_code, str)
            and self.product_code.isdigit()
        ):
            self.product_code = normalize_barcode(self.product_code)

    def clean(self, *args, **kwargs):
        # dict to store all ValidationErrors
        validation_errors = utils.merge_validation_errors(
            price_validators.validate_price_product_code_or_category_tag_rules(self),
            price_validators.validate_price_price_rules(self),
            price_validators.validate_price_date_rules(self),
            price_validators.validate_price_location_rules(self),
            price_validators.validate_price_proof_rules(self),
        )
        # return
        if bool(validation_errors):
            raise ValidationError(validation_errors)
        super().clean(*args, **kwargs)

    def set_product(self):
        if self.product_code:
            from open_prices.products.models import Product

            product, created = Product.objects.get_or_create(code=self.product_code)
            self.product = product

    def set_location(self):
        if self.location_osm_id and self.location_osm_type:
            from open_prices.locations import constants as location_constants
            from open_prices.locations.models import Location

            location, created = Location.objects.get_or_create(
                type=location_constants.TYPE_OSM,
                osm_id=self.location_osm_id,
                osm_type=self.location_osm_type,
            )
            self.location = location

    def save(self, *args, **kwargs):
        """
        - normalize product_code
        - run validations
        - set product (create if needed)
        - set location (create if needed)
        """
        self.normalize_product_code()
        self.full_clean()
        # self.set_proof()  # should already exist
        self.set_product()
        self.set_location()
        self.set_is_duplicate_of()
        super().save(*args, **kwargs)

    def set_tag(self, tag: str, save: bool = True):
        if tag not in self.tags:
            self.tags.append(tag)
            if save:
                self._change_reason = "Price.set_tag() method"
                self.save(update_fields=["tags"])
            return True
        return False

    def update_tags(self):
        changes = False
        # challenge tags (only if ongoing)
        challenge_qs = Challenge.objects.is_ongoing()
        if challenge_qs.exists():
            for challenge in challenge_qs:
                if self.in_challenge(challenge):
                    # update the price
                    success = self.set_tag(challenge.tag, save=False)
                    if success:
                        changes = True
                    # update the price's proof
                    if self.proof:
                        self.proof.set_tag(challenge.tag, save=True)  # important
        # save
        if changes:
            self._change_reason = "Price.update_tags() method"
            self.save(update_fields=["tags"])

    def has_category_tag(self, category_tag_list: list):
        if (
            self.type == price_constants.TYPE_CATEGORY
            and self.category_tag in category_tag_list
        ):
            return True
        elif (
            self.type == price_constants.TYPE_PRODUCT
            and self.product
            and self.product.categories_tags
        ):
            if set(self.product.categories_tags) & set(category_tag_list):
                return True
        return False

    def has_location(self, location_id_list: list):
        if self.location_id and self.location_id in location_id_list:
            return True
        return False

    def in_challenge(self, challenge: Challenge):
        return (
            self.created >= challenge.start_date_with_time
            and self.created <= challenge.end_date_with_time
            and (
                not challenge.categories or self.has_category_tag(challenge.categories)
            )
            and (
                not challenge.location_id_list()
                or self.has_location(challenge.location_id_list())
            )
        )

    def set_is_duplicate_of(self):
        """Look for duplicate prices and set the duplicate_of field
        accordingly.

        We consider `self` to be a duplicate of another price if:
        - it has the same location (osm_id and osm_type), date, currency and
          price information (price, discount type, is discounted, price
          without discount), product code/category tag, labels tags, and
          origins tags
        - it was created later than the other price (we keep the first one)
        """
        # Look for possible duplicates
        possible_duplicates = (
            Price.objects.filter(
                type=self.type,
                location_id=self.location_id,
                date=self.date,
                currency=self.currency,
                price=self.price,
                price_per=self.price_per,
                price_is_discounted=self.price_is_discounted,
                price_without_discount=self.price_without_discount,
                discount_type=self.discount_type,
                product_code=self.product_code,
                category_tag=self.category_tag,
                labels_tags=self.labels_tags,
                origins_tags=self.origins_tags,
                # Check that at least location and date are set,
                # otherwise it doesn't make much sense to consider these
                # prices as duplicates
                location_id__isnull=False,
                date__isnull=False,
            )
            .exclude(id=self.id)
            # oldest first
            .order_by("id")
        )
        duplicate = possible_duplicates.first()
        if duplicate is not None and duplicate.created < self.created:
            # Set the duplicate_of field to the first found duplicate
            self.duplicate_of = duplicate

    def get_history_list(self):
        return history.build_instance_history_list(self)


@receiver(signals.post_save, sender=Price)
def price_post_create_increment_counts(sender, instance, created, **kwargs):
    if created:
        if instance.owner:
            User.objects.filter(user_id=instance.owner).update(
                price_count=F("price_count") + 1
            )
        if instance.proof_id:
            Proof.objects.filter(id=instance.proof_id).update(
                price_count=F("price_count") + 1
            )
        if instance.product_id:
            Product.objects.filter(id=instance.product_id).update(
                price_count=F("price_count") + 1
            )
        if instance.location_id:
            Location.objects.filter(id=instance.location_id).update(
                price_count=F("price_count") + 1
            )
    else:
        # what about if we update the proof, product or location? (owner cannot be updated)
        # the update_fields is often not set, so we cannot rely on it
        pass


@receiver(signals.post_save, sender=Price)
def price_post_create_update_tags(sender, instance, created, **kwargs):
    if created:
        async_task(
            "open_prices.prices.tasks.update_tags",
            instance,
        )


@receiver(signals.pre_delete, sender=Price)
def price_pre_delete_update_price_tag(sender, instance, **kwargs):
    instance.price_tags.update(
        status=None,
        # price_id=None,  # will be done in the CASCADE
    )


@receiver(signals.post_delete, sender=Price)
def price_post_delete_decrement_counts(sender, instance, **kwargs):
    if instance.owner:
        User.objects.filter(user_id=instance.owner, price_count__gt=0).update(
            price_count=F("price_count") - 1
        )
    if instance.proof_id:
        Proof.objects.filter(id=instance.proof_id, price_count__gt=0).update(
            price_count=F("price_count") - 1
        )
    if instance.product_id:
        Product.objects.filter(id=instance.product_id, price_count__gt=0).update(
            price_count=F("price_count") - 1
        )
    if instance.location_id:
        Location.objects.filter(id=instance.location_id, price_count__gt=0).update(
            price_count=F("price_count") - 1
        )


@receiver(signals.post_delete, sender=Price)
def price_post_delete_update_duplicate_of(sender, instance, **kwargs):
    """When a price is deleted, we need to update the duplicate_of field
    of any prices that were marked as duplicates of this price.
    We set their duplicate_of field to None and save the price, so that
    the search for possible duplicates is run again."""
    # Sort by created descending, so that the most recent price is
    # re-evaluated first
    for price in Price.objects.filter(duplicate_of_id=instance.id).order_by("-created"):
        price.duplicate_of = None
        price.save(update_fields=["duplicate_of"])
