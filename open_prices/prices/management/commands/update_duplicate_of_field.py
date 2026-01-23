import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Count

from open_prices.prices.models import Price


class Command(BaseCommand):
    """Refresh the `duplicate_of_id` field for all prices, by saving them
    trigger any updates."""

    help = "Refresh the `duplicate_of_id` field for all prices."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Updating duplicate_of field for all prices...")

        filter_fields = [
            "type",
            "location_id",
            "date",
            "currency",
            "price",
            "price_per",
            "price_is_discounted",
            "price_without_discount",
            "discount_type",
            "product_code",
            "category_tag",
            "labels_tags",
            "origins_tags",
        ]

        # Group by relevant fields to find duplicates
        duplicates = (
            Price.objects.values(*filter_fields)
            .annotate(duplicate_count=Count("id"))
            .filter(duplicate_count__gt=1)
        )

        for item in tqdm.tqdm(
            duplicates.values_list(*filter_fields),
            desc="Processing duplicate groups",
        ):
            filters = dict(zip(filter_fields, item, strict=False))
            for price in Price.objects.filter(**filters).order_by("-id"):
                # Only save if duplicate_of_id is not already set
                if price.duplicate_of_id is None:
                    price.save()
