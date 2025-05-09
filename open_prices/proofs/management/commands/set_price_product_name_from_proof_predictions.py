from django.core.management.base import BaseCommand

from open_prices.prices.models import Price
from open_prices.proofs.models import PriceTag, ReceiptItem

price_tag_qs = (
    PriceTag.objects.status_linked_to_price()
    .exclude(price__isnull=True)
    .has_price_product_name_empty()
)
receipt_item_qs = (
    ReceiptItem.objects.status_linked_to_price()
    .exclude(price__isnull=True)
    .has_price_product_name_empty()
)


def stats():
    print("Prices with product_name:", Price.objects.has_product_name().count())
    print("PriceTag with a price without a product_name:", price_tag_qs.all().count())
    print(
        "ReceiptItem with a price without a product_name:",
        receipt_item_qs.all().count(),
    )


class Command(BaseCommand):
    """
    Some prices are linked to a proof PriceTag or ReceiptItem.
    Both contain a product_name prediction.
    But when using the match_price_tag_with_existing_prices & match_receipt_items_with_existing_prices  # noqa
    management commands, we don't set the product_name on the price.
    This command will set the product_name on the price if it is not already set.  # noqa
    """

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write("=== Stats before ===")
        stats()

        # Step 1: PriceTag
        self.stdout.write("=== Running script on PriceTags...")
        for price_tag in price_tag_qs.all():
            if price_tag.get_predicted_product_name():
                price_tag.price.product_name = price_tag.get_predicted_product_name()
                price_tag.price.save(update_fields=["product_name"])

        # Step 2: ReceiptItem
        self.stdout.write("=== Running script on ReceiptItems...")
        for receipt_item in receipt_item_qs.all():
            if receipt_item.get_predicted_product_name():
                receipt_item.price.product_name = (
                    receipt_item.get_predicted_product_name()
                )
                receipt_item.price.save(update_fields=["product_name"])

        self.stdout.write("=== Stats after ===")
        stats()
