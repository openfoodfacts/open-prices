import sys
from collections import Counter

from django.core.management.base import BaseCommand

from open_prices.prices.constants import TYPE_CATEGORY, TYPE_PRODUCT
from open_prices.proofs.models import PriceTag, Proof


def stats():
    sys.stdout.write("PriceTag", PriceTag.objects.count())
    sys.stdout.write("Proof PRICE_TAG", Proof.objects.filter(type="PRICE_TAG").count())
    sys.stdout.write(
        "PriceTag per status",
        Counter(PriceTag.objects.all().values_list("status", flat=True)),
    )
    sys.stdout.write(
        "PriceTag without a price_id",
        PriceTag.objects.filter(price_id__isnull=False).count(),
    )


class Command(BaseCommand):
    """
    for each proof
    try to match generated price_tags with existing prices
    - skip proofs without price_tags or without prices
    - skip price_tags that already have a price_id or that have no predictions
    - finally loop on each price and try to match with the price_tag prediction data  # noqa
    """

    help = "Match price tags with existing prices."

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write("Stats before...")
        stats()

        self.stdout.write("Running...")
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
                        price_tag_prediction_data = price_tag.predictions.first().data
                        for price in proof.prices.all():
                            if price.price_tags.count() > 0:
                                continue
                            elif (
                                price.type == TYPE_PRODUCT
                                and (
                                    price.product_code
                                    == price_tag_prediction_data["barcode"]
                                )
                                and (
                                    str(price.price)
                                    == str(price_tag_prediction_data["price"])
                                )
                            ):
                                price_tag.price_id = price.id
                                price_tag.status = 1
                                price_tag.save()
                                break
                            elif (
                                price.type == TYPE_CATEGORY
                                and (
                                    price.category_tag
                                    == price_tag_prediction_data["product"]
                                )
                                and (
                                    str(price.price)
                                    == str(price_tag_prediction_data["price"])
                                )
                            ):
                                price_tag.price_id = price.id
                                price_tag.status = 1
                                price_tag.save()
                                break
                            else:
                                continue

        self.stdout.write("Stats after...")
        stats()
