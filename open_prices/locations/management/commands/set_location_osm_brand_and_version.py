import time

from django.core.management.base import BaseCommand

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


class Command(BaseCommand):
    help = "Init Location osm_brand & osm_version fields (depending on it's creation date!)."

    def handle(self, *args, **options) -> None:  # type: ignore
        qs = Location.objects.has_type_osm()
        self.stdout.write(f"Found {qs.count()} OSM locations...")
        qs = qs.filter(osm_version=None)
        self.stdout.write(
            f"Of which {qs.count()} have their osm_version field empty..."
        )

        for location in qs.all():
            response = common_openstreetmap.get_historical_location_from_openstreetmap(
                location.osm_id, location.osm_type, location.created
            )
            if response:
                location.osm_brand = response.tag("brand")
                location.osm_version = response.version()
                location.save(update_fields=["osm_brand", "osm_version"])
            else:
                self.stdout.write(f"Could not find historical data for {location}")
            time.sleep(1)  # be nice to the OSM API
