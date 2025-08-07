import argparse

from django.core.management.base import BaseCommand

from open_prices.prices.models import Price
from open_prices.proofs.models import Proof


class Command(BaseCommand):
    """Remove duplicated proofs, based on the provided filters.

    This script removes all prices and proofs (excluding the reference proof
    and associated prices) that have the same owner, date, and location ID as
    the reference proof. It is useful to clean up the database from duplicate
    proofs that may have been created by mistake.
    """

    help = "Remove duplicated proofs, based on a reference proof."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run the cleanup and apply changes, otherwise just show what would be done (dry run).",
            default=False,
        )
        parser.add_argument(
            "--proof-id",
            help="The proof ID to keep as a reference.",
            type=int,
            required=True,
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        apply = options["apply"]
        proof_id = options["proof_id"]

        proof = Proof.objects.get(pk=proof_id)

        self.stdout.write("=== Running script to remove duplicate proofs...")
        self.stdout.write(
            f"Owner: {proof.owner}, Date: {proof.date}, Proof ID: {proof_id}, Location ID: {proof.location_id}"
        )
        if not apply:
            self.stdout.write("Running in dry run mode. Use --apply to apply changes.")

        self.remove_duplicates(ref_proof=proof, apply=apply)

    def remove_duplicates(self, ref_proof: Proof, apply: bool = False) -> None:
        self.stdout.write("Number of proofs before cleanup: %d" % Proof.objects.count())
        self.stdout.write("Number of prices before cleanup: %d" % Price.objects.count())

        prices_to_delete = (
            Price.objects.filter(
                proof__owner=ref_proof.owner,
                proof__date=ref_proof.date,
                proof__location_id=ref_proof.location_id,
            )
            .exclude(proof__id=ref_proof.id)
            .select_related("proof")
            .all()
        )

        proof_ids_to_delete = set(prices_to_delete.values_list("proof_id", flat=True))

        self.stdout.write(
            f"Found {len(prices_to_delete)} prices to delete associated with {len(proof_ids_to_delete)} proofs."
        )

        self.stdout.write(
            "Proof IDs to delete: %s" % ", ".join(map(str, proof_ids_to_delete))
        )
        self.stdout.write(
            "Prices to delete: %s"
            % ", ".join(map(str, prices_to_delete.values_list("id", flat=True)))
        )

        if apply:
            # Delete prices first to avoid foreign key constraints
            prices_to_delete.delete()
            self.stdout.write("Deleted %d prices." % prices_to_delete.count())

            # Now delete the proofs
            Proof.objects.filter(id__in=proof_ids_to_delete).delete()
            self.stdout.write("Deleted %d proofs." % len(proof_ids_to_delete))

        self.stdout.write("Number of proofs after cleanup: %d" % Proof.objects.count())
        self.stdout.write("Number of prices after cleanup: %d" % Price.objects.count())
