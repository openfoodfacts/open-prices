import time

from django.core.management.base import BaseCommand

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location
from open_prices.locations.tasks import fetch_and_save_data_from_openstreetmap


class Command(BaseCommand):
    """
    Usage: python manage.py detect_location_osm_version_change
    """

    help = "Detect Locations that may have changed (rebranded) on OSM, based on their OSM version change. Small changes are fetched & saved automatically; big changes are only reported, for manual review. This command does not create new Locations."

    def handle(self, *args, **options) -> None:  # type: ignore
        qs = Location.objects.has_type_osm()
        self.stdout.write(f"Found {qs.count()} OSM locations...")
        qs = qs.exclude(osm_version=None)
        self.stdout.write(
            f"Of which {qs.count()} have their osm_version field filled..."
        )

        has_osm_change_counter = 0
        has_big_osm_change_counter = 0
        deleted_counter = 0
        for index, location in enumerate(qs.all()):
            try:
                # we get the current (latest) version of the location
                response = common_openstreetmap.get_location_from_osm(
                    location.osm_id, location.osm_type, history=False
                )
                if response:
                    osm_data = {
                        "version": response.version(),
                        "version_date": response.timestamp(),
                        "name": response.tag("name"),
                        "brand": response.tag("brand"),
                        "tag_value": response.tag(location.osm_tag_key),
                        "lat": response.lat(),
                        "lon": response.lon(),
                    }
                    # has change
                    if location.osm_version != osm_data["version"]:
                        self.stdout.write(
                            f"=== {location.id} / {location.osm_type} / {location.osm_id}"
                        )
                        has_osm_change_counter += 1
                        # big change
                        if common_openstreetmap.has_big_osm_change(location, osm_data):
                            has_big_osm_change_counter += 1
                            for field, new_value in osm_data.items():
                                old_value = getattr(location, f"osm_{field}")
                                if old_value != new_value:
                                    self.stdout.write(
                                        f"{field}: {old_value} -> {new_value}"
                                    )
                        # small change: fetch full data and update the location
                        else:
                            fetch_and_save_data_from_openstreetmap(
                                location, existing_osm_response=response
                            )
                            self.stdout.write("Small change, location updated!")

                else:
                    self.stdout.write(f"Could not find current OSM data for {location}")
                if index and (index % 100 == 0):
                    print(f"{index} / {qs.count()}")
                time.sleep(1)  # be nice to the OSM API
            except Exception as e:
                if common_openstreetmap.is_deleted_osm_error(e):
                    deleted_counter += 1
                    self.stdout.write(f"=== {location} === deleted on OSM (410 Gone)")
                else:
                    self.stdout.write(f"Error with {location}: {e}")
        self.stdout.write(f"Total locations with OSM changes: {has_osm_change_counter}")
        self.stdout.write(
            f"Total locations with big OSM changes: {has_big_osm_change_counter}"
        )
        self.stdout.write(f"Total locations deleted on OSM: {deleted_counter}")
