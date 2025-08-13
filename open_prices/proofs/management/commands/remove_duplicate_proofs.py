import argparse
import hashlib

from django.core.management.base import BaseCommand

from open_prices.prices.models import Price
from open_prices.proofs.models import Proof


def compute_image_md5(file_path: str) -> str:
    """Compute the MD5 hash of an image file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


class Command(BaseCommand):
    """Remove duplicated proofs, based on the provided filters.

    This script removes all prices and proofs (excluding the reference proof
    and associated prices) that have the same owner, date, type and location ID
    as the reference proof. It is useful to clean up the database from
    duplicate proofs that may have been created by mistake.

    By default, it checks the MD5 hash of the images to ensure that only
    identical images are considered duplicates. If you want to remove
    duplicates based on metadata only (owner, date, type, location ID), you
    can disable the MD5 check with the `--no-md5-check` option.

    Before running this script, you should ensure that no other valid proof
    was uploaded by the same user on the same date, with the same type and
    location ID. This script will delete all proofs and prices that match
    these criteria, except for the reference proof provided by the user.
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
        parser.add_argument(
            "--no-md5-check",
            action="store_false",
            help="Disable MD5 check between images. "
            "This is useful if you want to remove duplicates based on metadata only, "
            "without checking if the images are actually identical.",
            dest="md5_check",
            default=True,
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        apply = options["apply"]
        proof_id = options["proof_id"]
        md5_check = options["md5_check"]

        proof = Proof.objects.get(pk=proof_id)

        self.stdout.write("=== Running script to remove duplicate proofs...")
        self.stdout.write(
            f"Owner: {proof.owner}, Date: {proof.date}, Proof ID: {proof_id}, Type: {proof.type}, Location ID: {proof.location_id}"
        )
        if not apply:
            self.stdout.write("Running in dry run mode. Use --apply to apply changes.")

        self.remove_duplicates(ref_proof=proof, apply=apply, md5_check=md5_check)

    def remove_duplicates(
        self, ref_proof: Proof, apply: bool = False, md5_check: bool = True
    ) -> None:
        self.stdout.write("Number of proofs before cleanup: %d" % Proof.objects.count())
        self.stdout.write("Number of prices before cleanup: %d" % Price.objects.count())
        self.stdout.write(f"MD5 check enabled: {md5_check}")

        proofs_to_delete = (
            Proof.objects.filter(
                owner=ref_proof.owner,
                date=ref_proof.date,
                type=ref_proof.type,
                location_id=ref_proof.location_id,
            )
            .exclude(id=ref_proof.id)
            .all()
        )

        if md5_check:
            # Filter proofs based on MD5 hash of the image
            ref_image_md5 = compute_image_md5(ref_proof.file_path_full)
            proofs_to_delete = [
                proof
                for proof in proofs_to_delete
                if compute_image_md5(proof.file_path_full) == ref_image_md5
            ]

            self.stdout.write(
                f"After MD5 check, {len(proofs_to_delete)} proofs remain to be deleted."
            )

        prices_to_delete = Price.objects.filter(proof__in=proofs_to_delete).all()

        self.stdout.write(
            f"Found {len(prices_to_delete)} prices to delete associated with {len(proofs_to_delete)} proofs."
        )

        self.stdout.write(
            "Proof IDs to delete: %s"
            % ", ".join(map(str, [proof.id for proof in proofs_to_delete]))
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
            for proof in proofs_to_delete:
                proof.delete()
            self.stdout.write("Deleted %d proofs." % len(proofs_to_delete))

        self.stdout.write("Number of proofs after cleanup: %d" % Proof.objects.count())
        self.stdout.write("Number of prices after cleanup: %d" % Price.objects.count())
