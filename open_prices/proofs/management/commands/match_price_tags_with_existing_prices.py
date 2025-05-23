from collections import Counter

from django.core.management.base import BaseCommand

from open_prices.prices import constants as price_constants
from open_prices.proofs.models import PriceTag, Proof
from open_prices.proofs.utils import (
    match_category_price_tag_with_category_price,
    match_price_tag_with_price,
    match_product_price_tag_with_product_price,
)

proof_qs = (
    Proof.objects.has_type_price_tag()
    .with_stats()
    .filter(price_count_annotated__gt=0, price_tag_count_annotated__gt=0)
)


def stats():
    print("PriceTag:", PriceTag.objects.count())
    print("Proof PRICE_TAG:", Proof.objects.has_type_price_tag().count())
    print("Proof PRICE_TAG with prices & price_tags:", proof_qs.all().count())
    print(
        "PriceTag per status:",
        Counter(PriceTag.objects.all().values_list("status", flat=True)),
    )
    print(
        "PriceTag without a price_id:",
        PriceTag.objects.filter(price_id__isnull=True).count(),
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
        self.stdout.write("=== Stats before ===")
        stats()

        self.stdout.write(
            "=== Running matching script on all PRICE_TAG proofs with prices & price_tags..."
        )
        proof_qs = Proof.objects.has_type_price_tag().prefetch_related(
            "prices", "price_tags", "price_tags__predictions"
        )
        for index, proof in enumerate(
            proof_qs.prefetch_related("price_tags__predictions").all()
        ):
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
                        elif (
                            price.type == price_constants.TYPE_PRODUCT
                            and match_product_price_tag_with_product_price(
                                price_tag, price
                            )
                        ):
                            price_tag.price_id = price.id
                            price_tag.status = 1
                            price_tag.save()
                            break
                        # match category price
                        elif (
                            price.type == price_constants.TYPE_CATEGORY
                            and match_category_price_tag_with_category_price(
                                price_tag, price
                            )
                        ):
                            price_tag.price_id = price.id
                            price_tag.status = 1
                            price_tag.save()
                            break
                        # match only on price
                        elif match_price_tag_with_price(price_tag, price):
                            price_tag.price_id = price.id
                            price_tag.status = 1
                            price_tag.save()
                            break
            if index % 500 == 0:
                self.stdout.write(f"Processed {index} proofs")

        self.stdout.write("=== Stats after ===")
        stats()
