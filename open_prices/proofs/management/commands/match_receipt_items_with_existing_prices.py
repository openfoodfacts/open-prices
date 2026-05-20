from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import F

from open_prices.proofs.models import Proof, ReceiptItem
from open_prices.proofs.utils import match_receipt_item_with_price

proof_qs = (
    Proof.objects.has_type_receipt()
    .prefetch_related("prices", "receipt_items")
    .with_stats()
    .filter(price_count_annotated__gt=0, receipt_item_count_annotated__gt=0)
    .exclude(price_count_annotated=F("receipt_item_count_annotated"))
)


def stats():
    print("ReceiptItem:", ReceiptItem.objects.count())
    print("Proof RECEIPT:", Proof.objects.has_type_receipt().count())
    print("Proof RECEIPT with prices & receipt_items:", proof_qs.all().count())
    print(
        "ReceiptItem per status:",
        Counter(ReceiptItem.objects.all().values_list("status", flat=True)),
    )
    print(
        "ReceiptItem without a price_id:",
        ReceiptItem.objects.filter(price_id__isnull=True).count(),
    )


class Command(BaseCommand):
    """
    For each proof...
    try to match generated receipt_items with existing prices
    - skip proofs without receipt_items or without prices
    - skip receipt_items that already have a price_id or that have no predictions
    - finally loop on each price and try to match with the receipt_item prediction data  # noqa
    """

    help = "Match receipt items with existing prices."

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write("=== Stats before ===")
        stats()

        self.stdout.write(
            "=== Running matching script on all RECEIPT proofs with prices & receipt_items..."
        )
        for index, proof in enumerate(proof_qs):
            for receipt_item in proof.receipt_items.filter(
                price_id__isnull=True
            ).exclude(predicted_data__isnull=True):
                for price in proof.prices.all():
                    # skip if price already has a receipt_item match
                    if price.receipt_items.count() > 0:
                        continue
                    # match only on price
                    elif match_receipt_item_with_price(receipt_item, price):
                        receipt_item.price_id = price.id
                        receipt_item.status = 1
                        receipt_item.save()
                        break
            if index % 500 == 0:
                self.stdout.write(f"Processed {index} proofs")

        self.stdout.write("=== Stats after ===")
        stats()
