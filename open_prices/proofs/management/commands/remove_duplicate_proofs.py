import argparse

from django.core.management.base import BaseCommand
from django.db.models import Count

from open_prices.prices.models import Price
from open_prices.proofs.models import Proof


class Command(BaseCommand):
    """Remove duplicated proofs.

    This script removes proofs that have the same owner, date, type and
    location and image MD5 hash: only the first uploaded proof of the group
    (named reference proof) is kept.

    All prices associated with these proofs are also updated to point to the
    reference proof.

    It is useful to clean up the database from duplicate proofs that may have
    been created by mistake.
    """

    help = "Remove duplicated proofs."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run the cleanup and apply changes, otherwise just show what would be done (dry run).",
            default=False,
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        apply = options["apply"]

        # Fetch all proofs for which at least one other proof has the same
        # owner, date, type, location and image MD5 hash.
        # First, group by these fields and count the number of proofs in each
        # group. Then, filter groups with more than one proof (i.e.
        # duplicates), and ignore proofs with null image MD5 hash.
        proof_groups = (
            Proof.objects.values(
                "owner",
                "date",
                "type",
                "location_id",
                "image_md5_hash",
            )
            .annotate(proof_count=Count("*"))
            .filter(proof_count__gt=1)
            .filter(image_md5_hash__isnull=False)
        )
        moved_price_count = 0
        deleted_proof_count = 0
        for proof_group in proof_groups:
            # Fetch all proofs in this group
            # Order by ID to keep the first uploaded proof as reference proof
            proofs = list(
                Proof.objects.filter(
                    owner=proof_group["owner"],
                    date=proof_group["date"],
                    type=proof_group["type"],
                    location_id=proof_group["location_id"],
                    image_md5_hash=proof_group["image_md5_hash"],
                ).order_by("id")
            )
            group_moved_price_count, group_deleted_proof_count = self.remove_duplicates(
                proofs=proofs, apply=apply
            )
            moved_price_count += group_moved_price_count
            deleted_proof_count += group_deleted_proof_count

        self.stdout.write(
            f"Total moved prices: {moved_price_count}, total deleted proofs: {deleted_proof_count}."
        )

    def remove_duplicates(
        self, proofs: list[Proof], apply: bool = False
    ) -> tuple[int, int]:
        if len(proofs) < 2:
            raise ValueError("At least two proofs are required to remove duplicates.")

        ref_proof = proofs[0]  # Keep the first proof as reference
        proofs_to_delete = proofs[1:]  # The rest will be deleted
        self.stdout.write(
            f"Found {len(proofs_to_delete)} proofs to delete (excluding the reference proof, ID: {ref_proof.id})."
        )

        prices_to_move = Price.objects.filter(proof__in=proofs_to_delete).all()

        self.stdout.write(
            f"Found {len(prices_to_move)} prices to move and {len(proofs_to_delete)} proofs to delete."
        )

        self.stdout.write(
            "Proof IDs to delete: {}".format(
                ", ".join(map(str, [proof.id for proof in proofs_to_delete]))
            )
        )
        self.stdout.write(
            "Prices to move: {}".format(
                ", ".join(map(str, prices_to_move.values_list("id", flat=True)))
            )
        )

        if apply:
            # Update proof_id for each price to point to the reference proof
            for price in prices_to_move:
                price.proof = ref_proof
                price._change_reason = "remove_duplicate_proofs command"
                price.save()

            # Now delete the proofs
            for proof in proofs_to_delete:
                proof._change_reason = "remove_duplicate_proofs command"
                proof.delete()

        return len(prices_to_move), len(proofs_to_delete)
