from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Count, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task
from openfoodfacts.barcode import normalize_barcode

# Import custom lookups so that they are registered
from open_prices.common import lookups  # noqa: F401
from open_prices.common.db_func import LevenshteinLessEqual
from open_prices.products import constants as product_constants


class ProductQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_stats(self):
        return self.annotate(price_count_annotated=Count("prices", distinct=True))

    def fuzzy_barcode_search(
        self,
        code: str,
        max_distance: int = 3,
        limit: int | None = None,
        exclude_distance_0: bool = True,
    ):
        """Use the `levenshtein_less_equal` from the fuzzystrmatch extension
        to find Products with barcode that are similar to the given barcode.

        Results are ordered by increasing Levenshtein distance.

        :param code: The barcode to search for
        :param max_distance: The maximum Levenshtein distance to consider
        :param limit: The maximum number of results to return, or None for no
            limit
        :param exclude_distance_0: Whether to exclude results with distance 0
            (i.e. exact matches)
        :return: A queryset of Product with similar barcodes
        """

        # Easy way to prevent SQL injection and useless queries
        if not code.isdigit():
            return self.none()

        qs = (
            self.annotate(
                distance=LevenshteinLessEqual(
                    "code", code, max_distance, output_field=models.IntegerField()
                ),
            )
            .filter(distance__lte=max_distance)
            .order_by("distance")
        )

        if exclude_distance_0:
            qs = qs.exclude(distance=0)

        if limit:
            qs = qs[:limit]

        return qs


class Product(models.Model):
    ARRAY_FIELDS = ["categories_tags", "brands_tags", "labels_tags"]
    OFF_SCORE_FIELDS = [
        "nutriscore_grade",
        "ecoscore_grade",
        "nova_group",
        "unique_scans_n",
    ]
    COUNT_FIELDS = [
        "price_count",
        "price_currency_count",
        "location_count",
        "location_type_osm_country_count",
        "user_count",
        "proof_count",
    ]

    code = models.CharField(unique=True)

    source = models.CharField(
        max_length=10, choices=product_constants.SOURCE_CHOICES, blank=True, null=True
    )
    source_last_synced = models.DateTimeField(blank=True, null=True)

    product_name = models.CharField(blank=True, null=True)
    image_url = models.CharField(blank=True, null=True)
    product_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    product_quantity_unit = models.CharField(blank=True, null=True)
    categories_tags = ArrayField(
        base_field=models.CharField(), blank=True, default=list
    )
    brands = models.CharField(blank=True, null=True)
    brands_tags = ArrayField(base_field=models.CharField(), blank=True, default=list)
    labels_tags = ArrayField(base_field=models.CharField(), blank=True, default=list)

    nutriscore_grade = models.CharField(blank=True, null=True)
    ecoscore_grade = models.CharField(blank=True, null=True)
    nova_group = models.PositiveIntegerField(blank=True, null=True)
    unique_scans_n = models.PositiveIntegerField(default=0, blank=True, null=True)

    price_count = models.PositiveIntegerField(default=0)
    price_currency_count = models.PositiveIntegerField(default=0)
    location_count = models.PositiveIntegerField(default=0)
    location_type_osm_country_count = models.PositiveIntegerField(default=0)
    user_count = models.PositiveIntegerField(default=0)
    proof_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(ProductQuerySet)()

    class Meta:
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def set_default_values(self):
        for field_name in self.ARRAY_FIELDS:
            if getattr(self, field_name) is None:
                setattr(self, field_name, [])

    def normalize_code(self):
        """
        Normalize the barcode (remove leading zeros, pad to 8 or 13 digits)
        """
        if self.code and isinstance(self.code, str) and self.code.isdigit():
            self.code = normalize_barcode(self.code)

    def save(self, *args, **kwargs):
        """
        - set default values
        - normalize code
        - run validations
        """
        self.set_default_values()
        self.normalize_code()
        self.full_clean()
        super().save(*args, **kwargs)

    def price__min(self, exclude_discounted=False):
        if exclude_discounted:
            return self.prices.exclude_discounted().calculate_min()
        return self.prices.calculate_min()

    def price__max(self, exclude_discounted=False):
        if exclude_discounted:
            return self.prices.exclude_discounted().calculate_max()
        return self.prices.calculate_max()

    def price__avg(self, exclude_discounted=False):
        if exclude_discounted:
            return self.prices.exclude_discounted().calculate_avg()
        return self.prices.calculate_avg()

    def price__stats(self, exclude_discounted=False):
        if exclude_discounted:
            return self.prices.exclude_discounted().calculate_stats()
        return self.prices.calculate_stats()

    def update_price_count(self):
        self.price_count = self.prices.count()
        self.price_currency_count = (
            self.prices.values_list("currency", flat=True).distinct().count()
        )
        self.save(update_fields=["price_count", "price_currency_count"])

    def update_location_count(self):
        from open_prices.locations import constants as location_constants
        from open_prices.prices.models import Price

        self.location_count = (
            Price.objects.filter(product=self, location_id__isnull=False)
            .values_list("location_id", flat=True)
            .distinct()
            .count()
        )
        self.location_type_osm_country_count = (
            Price.objects.filter(
                product=self,
                location_id__isnull=False,
                location__type=location_constants.TYPE_OSM,
            )
            .values_list("location__osm_address_country", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["location_count", "location_type_osm_country_count"])

    def update_user_count(self):
        from open_prices.prices.models import Price

        self.user_count = (
            Price.objects.filter(product=self, owner__isnull=False)
            .values_list("owner", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["user_count"])

    def update_proof_count(self):
        from open_prices.prices.models import Price

        self.proof_count = (
            Price.objects.filter(product=self, proof_id__isnull=False)
            .values_list("proof_id", flat=True)
            .distinct()
            .count()
        )
        self.save(update_fields=["proof_count"])


@receiver(signals.post_save, sender=Product)
def product_post_create_fetch_and_save_data_from_openfoodfacts(
    sender, instance, created, **kwargs
):
    if not settings.TESTING:
        if created:
            async_task(
                "open_prices.products.tasks.fetch_and_save_data_from_openfoodfacts",
                instance,
            )
