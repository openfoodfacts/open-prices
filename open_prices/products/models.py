from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from open_prices.products import constants as product_constants


class Product(models.Model):
    code = models.CharField(unique=True, blank=True, null=True)

    source = models.CharField(max_length=10, choices=product_constants.SOURCE_CHOICES)
    source_last_synced = models.DateTimeField(blank=True, null=True)

    product_name = models.CharField(blank=True, null=True)
    image_url = models.CharField(blank=True, null=True)
    product_quantity = models.IntegerField(blank=True, null=True)
    product_quantity_unit = models.CharField(blank=True, null=True)
    categories_tags = ArrayField(models.CharField(), blank=True)
    brands = models.CharField(blank=True, null=True)
    brands_tags = ArrayField(models.CharField(), blank=True)
    labels_tags = ArrayField(models.CharField(), blank=True)

    nutriscore_grade = models.CharField(blank=True, null=True)
    ecoscore_grade = models.CharField(blank=True, null=True)
    nova_group = models.PositiveIntegerField(blank=True, null=True)
    unique_scans_n = models.PositiveIntegerField(blank=True, null=True)

    price_count = models.PositiveIntegerField(default=0, blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
