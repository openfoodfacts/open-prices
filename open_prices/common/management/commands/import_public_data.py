from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from open_prices.common.data_import import import_exports


class Command(BaseCommand):
    help = "Import public locations, proofs and prices JSONL exports into an empty database."

    def add_arguments(self, parser: ArgumentParser) -> None:
        for name in ("locations", "proofs", "prices"):
            parser.add_argument(
                f"--{name}",
                required=True,
                type=Path,
                help="Path to a .jsonl or .jsonl.gz export.",
            )
        parser.add_argument("--batch-size", type=int, default=1000)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate files and references without writing to the database.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        paths = {
            name: Path(options[name]) for name in ("locations", "proofs", "prices")
        }
        self.stdout.write("Validating public exports...")
        plan = import_exports(
            paths, batch_size=options["batch_size"], dry_run=options["dry_run"]
        )
        action = "Validated (no data written)" if options["dry_run"] else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: {plan.counts['locations']} locations, {plan.counts['proofs']} proofs, "
                f"{plan.counts['prices']} prices, {len(plan.product_codes)} referenced product codes."
            )
        )
        self.stdout.write(
            "Product metadata and proof images are not included in these exports; no external requests were made."
        )
