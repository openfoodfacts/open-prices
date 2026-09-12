import time

from django.core.management.base import BaseCommand

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


class Command(BaseCommand):
    """
    Usage: python manage.py detect_location_osm_version_change
    """

    help = "Detect Locations that may have changed (rebranded) on OSM, based on their OSM version change. This is a read-only, reporting-only command: it does not create anything."

    def handle(self, *args, **options) -> None:  # type: ignore
        qs = Location.objects.has_type_osm()
        self.stdout.write(f"Found {qs.count()} OSM locations...")
        qs = qs.exclude(osm_version=None)
        self.stdout.write(
            f"Of which {qs.count()} have their osm_version field filled..."
        )

        counter = 0
        for index, location in enumerate(qs.all()):
            try:
                # we get the current (latest) version of the location
                response = common_openstreetmap.get_location_from_openstreetmap(
                    location.osm_id, location.osm_type, history=False
                )
                if response:
                    osm_data = {
                        "version": response.version(),
                        "version_date": response.timestamp(),
                        "name": response.tag("name"),
                        "brand": response.tag("brand"),
                        "lat": response.lat(),
                        "lon": response.lon(),
                    }
                    if location.osm_tag_key:
                        osm_data["tag_value"] = response.tag(location.osm_tag_key)
                    if common_openstreetmap.has_big_osm_change(location, osm_data):
                        counter += 1
                        self.stdout.write(f"=== {location} ===")
                        for field, new_value in osm_data.items():
                            old_value = getattr(location, f"osm_{field}")
                            self.stdout.write(f"{field}: {old_value} -> {new_value}")
                else:
                    self.stdout.write(f"Could not find current OSM data for {location}")
                if index and (index % 100 == 0):
                    print(index)
                time.sleep(1)  # be nice to the OSM API
            except Exception as e:
                self.stdout.write(f"Error with {location}: {e}")
        self.stdout.write(f"Total locations with big OSM changes: {counter}")
