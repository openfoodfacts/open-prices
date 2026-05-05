from pathlib import Path

from django.core.management.base import BaseCommand

from open_prices.proofs.models import Proof
from open_prices.proofs.utils import compute_file_md5_from_path


class Command(BaseCommand):
    """This command computes the image md5 hash for Proofs that don't have it
    yet."""

    def handle(self, *args, **options) -> None:  # type: ignore
        updated = 0
        for proof in Proof.objects.filter(image_md5_hash__isnull=True):
            file_path = Path(proof.file_path_full)

            if not file_path.exists():
                self.stdout.write(f"File does not exist: {file_path}")
                continue

            updated += 1
            proof.image_md5_hash = compute_file_md5_from_path(file_path)
            self.stdout.write(
                f"Updated proof {proof.id} with MD5 {proof.image_md5_hash}"
            )
            proof._change_reason = "compute_missing_image_hash command"
            proof.save(update_fields=["image_md5_hash"])

        self.stdout.write(f"Updated {updated} proofs.")
