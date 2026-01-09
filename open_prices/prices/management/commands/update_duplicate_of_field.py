import tqdm
from django.core.management.base import BaseCommand

from open_prices.prices.models import Price


class Command(BaseCommand):
    """Refresh the `duplicate_of_id` field for all prices, by saving them
    trigger any updates."""

    help = "Refresh the `duplicate_of_id` field for all prices."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Updating duplicate_of field for all prices...")
        for price in tqdm.tqdm(Price.objects.all(), desc="prices"):
            if price.duplicate_of is None:
                price.save()
