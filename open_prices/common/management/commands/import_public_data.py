from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from open_prices.common.import_data import import_exports


class Command(BaseCommand):
    help = (
        "Import public locations, proofs and prices JSONL exports into a development "
        "PostgreSQL database with migrations applied. Location, proof (including draft) "
        "and price tables must be empty; existing products and local accounts are kept. "
        "Run before starting the app or workers, and keep input files unchanged during "
        "the import. Product metadata and proof images are not downloaded. "
        "See open_prices/common/import_data.py for implementation details."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        for name in ("locations", "proofs", "prices"):
            parser.add_argument(
                f"--{name}",
                required=True,
                type=Path,
                help="Path to a .jsonl or .jsonl.gz export.",
            )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Maximum records per batch write (default: 1000; must be positive).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Validate field values, duplicate IDs and references without writing "
                "to the database or advancing ID sequences."
            ),
        )
        parser.add_argument(
            "--allow-missing-references",
            action="store_true",
            help=(
                "Allow filtered exports by setting missing location, proof and "
                "duplicate-price references to NULL and reporting their count. "
                "By default, missing references cause an error."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        paths = {
            name: Path(options[name]) for name in ("locations", "proofs", "prices")
        }
        self.stdout.write("Validating public exports...")
        plan = import_exports(
            paths,
            batch_size=options["batch_size"],
            dry_run=options["dry_run"],
            allow_missing_references=options["allow_missing_references"],
        )
        action = "Validated (no data written)" if options["dry_run"] else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: {plan.counts['locations']} locations, {plan.counts['proofs']} proofs, "
                f"{plan.counts['prices']} prices, {len(plan.product_codes)} referenced product codes."
            )
        )
        if plan.missing_reference_count:
            action = "Would clear" if options["dry_run"] else "Cleared"
            self.stdout.write(
                f"{action} {plan.missing_reference_count} missing references."
            )
        self.stdout.write(
            "Product metadata and proof images are not included in these exports; no external requests were made."
        )
