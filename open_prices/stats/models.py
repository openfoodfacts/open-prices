from django.db import models
from django.utils import timezone
from solo.models import SingletonModel


class TotalStats(SingletonModel):
    price_count = models.PositiveIntegerField(default=0)
    price_barcode_count = models.PositiveIntegerField(default=0)
    price_category_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    product_with_price_count = models.PositiveIntegerField(default=0)
    location_count = models.PositiveIntegerField(default=0)
    location_with_price_count = models.PositiveIntegerField(default=0)
    proof_count = models.PositiveIntegerField(default=0)
    proof_with_price_count = models.PositiveIntegerField(default=0)
    user_count = models.PositiveIntegerField(default=0)
    user_with_price_count = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Total Stats"
        verbose_name_plural = "Total Stats"
