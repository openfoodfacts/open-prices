from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Count, signals
from django.dispatch import receiver
from django.utils import timezone
from django_q.tasks import async_task

from open_prices.products import constants as product_constants


class ProductQuerySet(models.QuerySet):
    def has_prices(self):
        return self.filter(price_count__gt=0)

    def with_stats(self):
        return self.annotate(price_count_annotated=Count("prices", distinct=True))


class Product(models.Model):
    ARRAY_FIELDS = ["categories_tags", "brands_tags", "labels_tags"]

    code = models.CharField(unique=True)

    source = models.CharField(
        max_length=10, choices=product_constants.SOURCE_CHOICES, blank=True, null=True
    )
    source_last_synced = models.DateTimeField(blank=True, null=True)

    product_name = models.CharField(blank=True, null=True)
    image_url = models.CharField(blank=True, null=True)
    product_quantity = models.IntegerField(blank=True, null=True)
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

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(ProductQuerySet)()

    class Meta:
        # managed = False
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def set_default_values(self):
        for field_name in self.ARRAY_FIELDS:
            if getattr(self, field_name) is None:
                setattr(self, field_name, [])

    def save(self, *args, **kwargs):
        """
        - set default values
        - run validations
        """
        self.set_default_values()
        self.full_clean()
        super().save(*args, **kwargs)


@receiver(signals.post_save, sender=Product)
def product_post_create_fetch_data_from_openfoodfacts(
    sender, instance, created, **kwargs
):
    if created:
        async_task(
            "open_prices.products.tasks.fetch_and_save_data_from_openfoodfacts",
            instance,
        )
