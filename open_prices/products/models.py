import datetime

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Count, Exists, OuterRef, Q, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task
from openfoodfacts.barcode import normalize_barcode

from open_prices.common import constants as common_constants
from open_prices.common.counts import (
    bulk_update_counts,
    count_subquery,
    update_counts,
)
from open_prices.common.db_func import LevenshteinLessEqual
from open_prices.common.managers import ApproximateCountQuerySet
from open_prices.products import constants as product_constants


class ProductQuerySet(ApproximateCountQuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)

    def created_by_open_prices(self):
        return self.filter(creator=settings.OFF_DEFAULT_USER)

    def with_stats(self):
        return self.annotate(price_count_annotated=Count("prices", distinct=True))

    def with_price_counts(self):
        """
        - price_count: number of prices
        - price_currency_count: number of distinct price currencies
        """
        from open_prices.prices.models import Price

        return self.annotate(
            price_count_annotated=count_subquery(Price, "product", Count("id")),
            price_currency_count_annotated=count_subquery(
                Price, "product", Count("currency", distinct=True)
            ),
        )

    def with_location_counts(self):
        """
        - location_count: number of distinct price locations
        - location_type_osm_country_count: number of distinct price location
        countries (OSM locations only)
        """
        from open_prices.locations import constants as location_constants
        from open_prices.prices.models import Price

        return self.annotate(
            location_count_annotated=count_subquery(
                Price, "product", Count("location_id", distinct=True)
            ),
            location_type_osm_country_count_annotated=count_subquery(
                Price,
                "product",
                Count(
                    "location__osm_address_country",
                    distinct=True,
                    filter=Q(location__type=location_constants.TYPE_OSM),
                ),
            ),
        )

    def with_user_count(self):
        """
        - user_count: number of distinct price owners
        """
        from open_prices.prices.models import Price

        return self.annotate(
            user_count_annotated=count_subquery(
                Price, "product", Count("owner", distinct=True)
            )
        )

    def with_proof_count(self):
        """
        - proof_count: number of distinct price proofs
        """
        from open_prices.prices.models import Price

        return self.annotate(
            proof_count_annotated=count_subquery(
                Price, "product", Count("proof_id", distinct=True)
            )
        )

    def with_counts(self):
        """
        All the COUNT_FIELDS
        """
        return (
            self.with_price_counts()
            .with_location_counts()
            .with_user_count()
            .with_proof_count()
        )

    def to_update_in_sync_task(
        self,
        code: str,
        flavor: str,
        product_source_last_modified: datetime.datetime = None,
    ):
        """
        Goal: OFF sync task, a product should be updated if:
        - is part of the current flavor sync (or if it has no source (created in Open Prices before OFF))
        - has been updated since the last sync (or has never been synced)

        Usage: open_prices/common/openfoodfacts.py:import_product_db
        """
        queryset = self.filter(code=code).filter(Q(source=flavor) | Q(source=None))
        if product_source_last_modified:
            queryset = queryset.filter(
                Q(source_last_synced__lt=product_source_last_modified)
                | Q(source_last_synced=None)
            )
        return queryset

    def for_update_task(self):
        """
        Goal: only update counts of products that have prices, to save (some) time.
        Also include products with a non-zero count, to reset the counts
        of products whose prices were all deleted.

        Usage: open_prices/common/tasks.py:update_product_counts_task
        """
        from open_prices.prices.models import Price

        has_counts = Q()
        for field in self.model.COUNT_FIELDS:
            has_counts |= Q(**{f"{field}__gt": 0})
        return self.filter(
            has_counts | Q(Exists(Price.objects.filter(product_id=OuterRef("pk"))))
        )

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
    product_quantity = models.IntegerField(blank=True, null=True)
    product_quantity_unit = models.CharField(blank=True, null=True)
    quantity = models.CharField(blank=True, null=True)
    categories_tags = ArrayField(
        base_field=models.CharField(), blank=True, default=list
    )
    brands = models.CharField(blank=True, null=True)
    brands_tags = ArrayField(base_field=models.CharField(), blank=True, default=list)
    labels_tags = ArrayField(base_field=models.CharField(), blank=True, default=list)

    nutriscore_grade = models.CharField(blank=True, null=True)
    ecoscore_grade = models.CharField(blank=True, null=True)
    nova_group = models.PositiveIntegerField(blank=True, null=True)
    creator = models.CharField(blank=True, null=True)
    unique_scans_n = models.PositiveIntegerField(default=0, blank=True, null=True)

    # denormalized counts (updated with signals and/or cronjobs)
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

    @classmethod
    def update_task(cls):
        """
        - Update product field counts
        - Some products are skipped (see queryset)
        - Only the products with changed counts are updated
        """
        return bulk_update_counts(
            cls.objects.for_update_task().with_counts(), cls.COUNT_FIELDS
        )

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
        update_counts(
            self,
            Product.objects.with_price_counts(),
            ["price_count", "price_currency_count"],
        )

    def update_location_count(self):
        update_counts(
            self,
            Product.objects.with_location_counts(),
            ["location_count", "location_type_osm_country_count"],
        )

    def update_user_count(self):
        update_counts(self, Product.objects.with_user_count(), ["user_count"])

    def update_proof_count(self):
        update_counts(self, Product.objects.with_proof_count(), ["proof_count"])


@receiver(signals.post_save, sender=Product)
def product_post_create_fetch_and_save_data_from_openfoodfacts(
    sender, instance, created, **kwargs
):
    if not settings.TESTING:
        if created:
            async_task(
                "open_prices.products.tasks.fetch_and_save_data_from_openfoodfacts",
                instance,
                group=common_constants.TASK_GROUP_FETCH_OPENFOODFACTS,
            )
