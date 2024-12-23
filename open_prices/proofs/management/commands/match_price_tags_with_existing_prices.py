from collections import Counter
from decimal import Decimal

from django.core.management.base import BaseCommand

from open_prices.prices.constants import TYPE_CATEGORY, TYPE_PRODUCT
from open_prices.prices.models import Price
from open_prices.proofs.models import PriceTag, Proof


def stats():
    print("PriceTag:", PriceTag.objects.count())
    print("Proof PRICE_TAG:", Proof.objects.has_type_price_tag().count())
    print(
        "PriceTag per status:",
        Counter(PriceTag.objects.all().values_list("status", flat=True)),
    )
    print(
        "PriceTag without a price_id:",
        PriceTag.objects.filter(price_id__isnull=True).count(),
    )


def match_decimal_with_float(price_decimal: Decimal, price_float: float) -> bool:
    return float(price_decimal) == price_float


def match_price_tag_with_product_price(price: Price, price_tag: PriceTag) -> bool:
    price_tag_prediction_data = price_tag.predictions.first().data
    return (
        price.type == TYPE_PRODUCT
        and (price.product_code == price_tag_prediction_data["barcode"])
        and match_decimal_with_float(price.price, price_tag_prediction_data["price"])
    )


def match_price_tag_with_category_price(price: Price, price_tag: PriceTag) -> bool:
    price_tag_prediction_data = price_tag.predictions.first().data
    return (
        price.type == TYPE_CATEGORY
        and (price.product_code == price_tag.predictions.first().data["product"])
        and match_decimal_with_float(price.price, price_tag_prediction_data["price"])
    )


class Command(BaseCommand):
    """
    For each proof...
    try to match generated price_tags with existing prices
    - skip proofs without price_tags or without prices
    - skip price_tags that already have a price_id or that have no predictions
    - finally loop on each price and try to match with the price_tag prediction data  # noqa
    """

    help = "Match price tags with existing prices."

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write("=== Stats before...")
        stats()

        self.stdout.write("=== Running matching script...")
        for proof in Proof.objects.has_type_price_tag().prefetch_related(
            "prices", "price_tags", "price_tags__predictions"
        ):
            if proof.price_tags.count() == 0:
                continue
            elif proof.prices.count() == 0:
                continue
            else:
                for price_tag in proof.price_tags.all():
                    if price_tag.price_id is not None:
                        continue
                    elif price_tag.predictions.count() == 0:
                        continue
                    else:
                        for price in proof.prices.all():
                            # skip if price already has a price_tag match
                            if price.price_tags.count() > 0:
                                continue
                            # match product price
                            elif match_price_tag_with_product_price(price, price_tag):
                                price_tag.price_id = price.id
                                price_tag.status = 1
                                price_tag.save()
                                break
                            # match category price
                            elif match_price_tag_with_category_price(price, price_tag):
                                price_tag.price_id = price.id
                                price_tag.status = 1
                                price_tag.save()
                                break
                            else:
                                continue

        self.stdout.write("=== Stats after...")
        stats()
