import argparse
from itertools import groupby

from django.core.management.base import BaseCommand

from open_prices.prices import constants as price_constants
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import PriceTag


class Command(BaseCommand):
    """Remove duplicate prices, only for prices associated with proof of type
    PRICE_TAG.

    This command currently only removes duplicate prices coming from the
    same proof, duplicate proofs are not handled yet.

    We first create a CTE (temporary Common Table Expression) to find all
    duplicate prices. Prices are considered as duplicates if their have the
    same (`product_code`/`category_tag`, `price`, `proof_id`).

    We then loop on each group of duplicate prices, keeping the first one
    (the one with the lowest ID) and removing the others. If any of the
    duplicate prices is linked to a price tag, we update the price tag to
    point to the first price instead of the removed one.

    This script currently only runs for prices of type PRODUCT, as there
    are valid cases where a proof has several prices for the same
    `category_tag` (e.g., several types of apple, and we don't have all
    varieties in Open Food Facts taxonomy).
    """

    help = "Remove duplicate prices, only for prices with proof of type PRICE_TAG."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run the cleanup and apply changes, otherwise just show what would be done (dry run).",
            default=False,
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        apply = options["apply"]

        self.stdout.write(
            "=== Running script to remove duplicate prices associated with PRICE_TAG proofs..."
        )
        if not apply:
            self.stdout.write("Running in dry run mode. Use --apply to apply changes.")

        # For the moment, only run it for PRODUCT prices, as there are valid
        # cases where a proof has several prices for the same
        # category_tag (ex: several types of apple, and we don't have all
        # varieties in Open Food Facts taxonomy).
        self.remove_duplicates(price_type=price_constants.TYPE_PRODUCT, apply=apply)

    def remove_duplicates(self, price_type: str, apply: bool = False) -> None:
        if price_type not in price_constants.TYPE_LIST:
            self.stdout.write(
                f"Price type {price_type} is not supported. Supported types are: {price_constants.TYPE_LIST}"
            )
            return

        comparison_field = price_constants.TYPE_FIELD_MAPPING[price_type]

        self.stdout.write(f"Removing duplicates for price type: {price_type}")
        self.stdout.write(
            "Number of prices (with proof of type PRICE_TAG) before cleanup: %d"
            % Price.objects.select_related("proof")
            .filter(proof__type=proof_constants.TYPE_PRICE_TAG)
            .count()
        )

        # Create a CTE to find duplicate prices. We use a raw SQL query
        # to find duplicates based on product_code (or category_tag), price,
        # and proof_id.
        duplicate_prices = Price.objects.raw(
            f"""WITH
                duplicated_products AS (
                    SELECT
                    t1.{comparison_field},
                    t1.price,
                    t1.proof_id,
                    COUNT(t1.id) AS count
                    FROM
                    prices as t1
                    JOIN proofs as t2 ON (t1.proof_id = t2.id)
                    WHERE
                    t1.type = '{price_type}'
                    AND t2.type = 'PRICE_TAG'
                    GROUP BY
                    (t1.{comparison_field}, t1.price, t1.proof_id)
                    HAVING
                    COUNT(t1.id) > 1
                )
                SELECT
                    t1.proof_id, t1.{comparison_field}, t1.id
                FROM
                    prices as t1
                JOIN duplicated_products as t2 ON (
                    t1.{comparison_field} = t2.{comparison_field}
                    AND t1.price = t2.price
                    AND t1.proof_id = t2.proof_id
                )
                ORDER BY
                    (t1.proof_id, t1.{comparison_field}, t1.id) ASC;
                """
        )

        deleted = 0
        price_tag_updated = 0

        # The list of prices is already ordered by proof_id, comparison_field
        # and id (ascending), so we can use groupby to group them.
        for key, price_group in groupby(
            duplicate_prices,
            key=lambda x: (x.proof_id, getattr(x, comparison_field)),
        ):
            price_list = list(price_group)
            proof_id, value = key
            self.stdout.write(
                f"Found {len(price_list)} duplicate prices for proof {proof_id} with {comparison_field} {value}"
            )
            if len(price_list) > 1:
                # We always keep the first uploaded price (price with the
                # lowest ID)
                first_price = price_list.pop(0)
                # All prices to remove are added to `to_remove`
                to_remove = []
                prices_linked_to_price_tag = []
                # First, fetch all price tags associated with any of the
                # duplicate prices. This is useful to update the price_id
                # of the price tags to the first price if needed.
                price_tags = PriceTag.objects.filter(
                    price_id__in=[price.id for price in price_list]
                ).all()

                for price in price_list:
                    if not any(
                        price_tag.price_id == price.id for price_tag in price_tags
                    ):
                        # There is no price tag linked to this price,
                        # so we can safely remove it.
                        to_remove.append(price)
                    else:
                        # Otherwise we keep it temporarily to update the
                        # price_tag.price_id field later.
                        prices_linked_to_price_tag.append(price)

                if prices_linked_to_price_tag:
                    # Theorically, there may be several price tags for the same
                    # proof and product code (ex: identical price tags on the
                    # same image, due to an incorrect detection by the object
                    # detection model).
                    # As this case should be rare, we don't delete these
                    # duplicate prices. The price tag can be deleted manually
                    # using an admin interface.
                    price_linked_to_price_tag = prices_linked_to_price_tag[0]
                    price_tag = [
                        price_tag
                        for price_tag in price_tags
                        if price_tag.price_id == price_linked_to_price_tag.id
                    ][0]
                    self.stdout.write(
                        f"Updating price tag {price_tag.id} to point to the first price {first_price.id} (previously {price_tag.price_id})"
                    )

                    if apply:
                        price_tag.price_id = first_price.id
                        price_tag.save()

                    to_remove.append(price_linked_to_price_tag)
                    price_tag_updated += 1

                if to_remove:
                    self.stdout.write(
                        f"Removing {len(to_remove)} duplicate prices for proof {proof_id} with {comparison_field} {value}"
                    )
                    deleted += len(to_remove)
                    for price in to_remove:
                        self.stdout.write(
                            f"Removing price {price.id} for proof {proof_id} with {comparison_field} {value}"
                        )
                    if apply:
                        Price.objects.filter(
                            id__in=[price.id for price in to_remove]
                        ).delete()

        self.stdout.write(f"Deleted {deleted} duplicate prices.")
        self.stdout.write(
            f"Updated {price_tag_updated} price tags to point to the first price."
        )
        self.stdout.write(
            "Number of prices (with proof of type PRICE_TAG) after cleanup: %d"
            % Price.objects.filter(proof__type=proof_constants.TYPE_PRICE_TAG).count()
        )
