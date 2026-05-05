import argparse

from django.core.management.base import BaseCommand
from openfoodfacts.barcode import normalize_barcode

from open_prices.prices.models import Price
from open_prices.products.models import Product


class Command(BaseCommand):
    """Normalize barcodes for the `products` and `prices` tables.

    This command will go through all `product_code` in the `prices` table and
    `code` in the `products` table, and normalize the barcodes (remove leading
    zeros, pad to 8 or 13 digits).
    """

    help = "Normalize barcodes for the `products` and `prices` tables."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run the normalization and apply changes, otherwise just show what would be done (dry run).",
            default=False,
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        apply = options["apply"]

        self.stdout.write("=== Running script to normalize barcodes...")
        if not apply:
            self.stdout.write("Running in dry run mode. Use --apply to apply changes.")

        self.normalize_barcodes(apply=apply)

    def normalize_barcodes(self, apply: bool = False) -> None:
        for price in Price.objects.has_type_product().all():
            if price.product_code and price.product_code.isdigit():
                normalized_code = normalize_barcode(price.product_code)
                if normalized_code != price.product_code:
                    self.stdout.write(
                        f"Price ID {price.id}: Normalizing barcode from {price.product_code} to {normalized_code}"
                    )
                    if apply:
                        price.product_code = normalized_code
                        # we also update `product_id` as we changed the
                        # barcode, and the product ID is updated automatically
                        # in `save()`
                        price.save(update_fields=["product_code", "product_id"])

        for product in Product.objects.all():
            if product.code and product.code.isdigit():
                normalized_code = normalize_barcode(product.code)
                if normalized_code != product.code:
                    if Product.objects.filter(code=normalized_code).exists():
                        self.stdout.write(
                            f"Product ID {product.id}: Normalizing barcode from {product.code} to {normalized_code} "
                            f"would create a duplicate product, deleting product ID {product.id}."
                        )
                        if apply:
                            product.delete()
                    else:
                        self.stdout.write(
                            f"Product ID {product.id}: Normalizing barcode from {product.code} to {normalized_code}"
                        )
                        if apply:
                            product.code = normalized_code
                            product.save(update_fields=["code"])
