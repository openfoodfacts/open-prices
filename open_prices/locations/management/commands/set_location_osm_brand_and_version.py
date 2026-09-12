import argparse
import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


class Command(BaseCommand):
    help = "Fill Location osm_brand, osm_version & osm_version_date fields (depending on its creation date!)."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Run and apply changes, otherwise just show what would be done (dry run).",
            default=False,
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        apply = options["apply"]

        self.stdout.write(
            "=== Running script to set Location osm_brand, osm_version & osm_version_date fields..."
        )
        if not apply:
            self.stdout.write("Running in dry run mode. Use --apply to apply changes.")

        qs = Location.objects.has_type_osm()
        self.stdout.write(f"Found {qs.count()} OSM locations")
        self.stdout.write(
            f"Of which {qs.filter(osm_brand=None).count()} have their osm_brand field empty..."
        )
        self.stdout.write(
            f"Of which {qs.filter(osm_version=None).count()} have their osm_version field empty..."
        )
        self.stdout.write(
            f"Of which {qs.filter(osm_version_date=None).count()} have their osm_version_date field empty..."
        )
        qs = qs.filter(
            Q(osm_brand=None) | Q(osm_version=None) | Q(osm_version_date=None)
        )
        self.stdout.write(f"Filtered down to {qs.count()} locations that need updates.")

        if apply:
            for index, location in enumerate(qs.all()):
                try:
                    response = (
                        common_openstreetmap.get_historical_location_from_openstreetmap(
                            location.osm_id, location.osm_type, location.created
                        )
                    )
                    if response:
                        location.osm_brand = response.tag("brand")
                        location.osm_version = response.version()
                        location.osm_version_date = response.timestamp()
                        location.save(
                            update_fields=[
                                "osm_brand",
                                "osm_version",
                                "osm_version_date",
                            ]
                        )
                    else:
                        self.stdout.write(
                            f"Could not find historical data for {location}"
                        )
                    if index % 100 == 0:
                        print(index)
                    time.sleep(1)  # be nice to the OSM API
                except Exception as e:
                    self.stdout.write(f"Error with {location}: {e}")
