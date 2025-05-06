from django.core.management.base import BaseCommand

from open_prices.prices.models import Price
from open_prices.proofs.models import PriceTag, ReceiptItem


def stats():
    print("Prices with product_name:", Price.objects.has_product_name().count())


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
        for price_tag in (
            PriceTag.objects.status_linked_to_price()
            .exclude(price__isnull=True)
            .has_price_product_name_empty()
        ):
            if price_tag.get_predicted_product_name():
                price_tag.price.product_name = price_tag.get_predicted_product_name()
                price_tag.price.save(update_fields=["product_name"])

        # Step 2: ReceiptItem
        for receipt_item in (
            ReceiptItem.objects.status_linked_to_price()
            .exclude(price__isnull=True)
            .has_price_product_name_empty()
        ):
            if receipt_item.get_predicted_product_name():
                receipt_item.price.product_name = (
                    receipt_item.get_predicted_product_name()
                )
                receipt_item.price.save(update_fields=["product_name"])

        self.stdout.write("=== Stats after ===")
        stats()
