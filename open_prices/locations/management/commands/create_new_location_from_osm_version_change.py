import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


class Command(BaseCommand):
    """
    Usage: python manage.py create_new_location_from_osm_version_change
    """

    help = "A location has changed (rebranded)? Create a new Location for it, based on its OSM version change."

    def handle(self, *args, **options) -> None:  # type: ignore
        qs = Location.objects.has_type_osm()
        self.stdout.write(f"Found {qs.count()} OSM locations...")
        qs = qs.exclude(osm_version=None)
        self.stdout.write(
            f"Of which {qs.count()} have their osm_version field filled..."
        )

        for index, location in enumerate(qs.all()):
            try:
                # we get the latest version of the location
                response = (
                    common_openstreetmap.get_historical_location_from_openstreetmap(
                        location.osm_id, location.osm_type, timezone.now()
                    )
                )
                if response:
                    # print(response.__dict__)
                    # compare with the location version at its creation date
                    # big change detected = version change + name or brand change  # noqa
                    if (response.version() != location.osm_version) and (
                        response.tag("name") != location.osm_name
                        or response.tag("brand") != location.osm_brand
                    ):
                        self.stdout.write(
                            f"{location}: version: {location.osm_version} -> {response.version()}"
                        )
                        self.stdout.write(
                            f"{location}: name: {location.osm_name} -> {response.tag('name')}"
                        )
                        self.stdout.write(
                            f"{location}: brand: {location.osm_brand} -> {response.tag('brand')}"
                        )
                else:
                    self.stdout.write(f"Could not find historical data for {location}")
                if index and (index % 100 == 0):
                    print(index)
                time.sleep(1)  # be nice to the OSM API
            except Exception as e:
                self.stdout.write(f"Error with {location}: {e}")
