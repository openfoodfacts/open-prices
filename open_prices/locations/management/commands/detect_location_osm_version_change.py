import time
from collections import Counter

from django.core.management.base import BaseCommand

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location
from open_prices.locations.tasks import fetch_and_save_data_from_openstreetmap


class Status:
    UNCHANGED = "unchanged"
    MINOR_CHANGE = "minor_change"
    MAJOR_CHANGE = "major_change"
    NOT_FOUND = "not_found"
    DELETED = "deleted"
    ERROR = "error"


class Command(BaseCommand):
    """
    Usage: python manage.py detect_location_osm_version_change
    """

    help = """
    Detect Locations that may have changed (rebranded) on OSM, based on their OSM version change.
    Minor changes are fetched & the location is updated.
    Major changes are only reported, for manual review.
    This command does not create new Locations.
    """

    def handle(self, *args, **options) -> None:  # type: ignore
        qs = Location.objects.has_type_osm()
        self.stdout.write(f"Found {qs.count()} OSM locations...")
        qs = qs.exclude(osm_version=None)
        self.stdout.write(
            f"Of which {qs.count()} have their osm_version field filled..."
        )

        counters = Counter()

        for index, location in enumerate(qs.all()):
            try:
                status = self._process_location(location)
            except Exception as e:
                if common_openstreetmap.is_deleted_osm_error(e):
                    status = Status.DELETED
                    self.stdout.write(f"=== {location} === deleted on OSM (410 Gone)")
                else:
                    status = Status.ERROR
                    self.stdout.write(f"Error with {location}: {e}")
            counters[status] += 1
            if index and (index % 100 == 0):
                print(f"{index} / {qs.count()}")
            time.sleep(1)  # be nice to the OSM API

        # done!
        self.stdout.write("=== Summary ===")
        self.stdout.write(f"Total locations processed: {sum(counters.values())}")
        self.stdout.write(
            f"Total locations unchanged on OSM: {counters[Status.UNCHANGED]}"
        )
        self.stdout.write(
            f"Total locations with minor OSM changes: {counters[Status.MINOR_CHANGE]}. They have been updated!"
        )
        self.stdout.write(
            f"Total locations with major OSM changes: {counters[Status.MAJOR_CHANGE]}"
        )
        self.stdout.write(
            f"Total locations not found on OSM: {counters[Status.NOT_FOUND]}"
        )
        self.stdout.write(f"Total locations deleted on OSM: {counters[Status.DELETED]}")
        self.stdout.write(f"Total locations with errors: {counters[Status.ERROR]}")

    def _process_location(self, location) -> str:
        """
        Fetch the current OSM data for `location`, compare it to what's
        stored, and either report a big change or persist a small one.

        Returns one of the Status values.
        """
        # we get the current (latest) version of the location
        response = common_openstreetmap.get_location_from_osm(
            location.osm_id, location.osm_type, history=False
        )
        if not response:
            self.stdout.write(f"Could not find current OSM data for {location}")
            return Status.NOT_FOUND

        osm_data = {
            "version": response.version(),
            "version_date": response.timestamp(),
            "name": response.tag("name"),
            "brand": response.tag("brand"),
            "lat": response.lat(),
            "lon": response.lon(),
            "tag_value": response.tag(location.osm_tag_key),
        }
        if location.osm_version == osm_data["version"]:
            return Status.UNCHANGED

        self.stdout.write(
            f"=== {location.id} / {location.osm_type} / {location.osm_id}"
        )
        if common_openstreetmap.has_major_osm_change(location, osm_data):
            for field, new_value in osm_data.items():
                old_value = getattr(location, f"osm_{field}")
                if old_value != new_value:
                    self.stdout.write(f"{field}: {old_value} -> {new_value}")
            return Status.MAJOR_CHANGE

        # small change: fetch full data and update the location
        location._change_reason = "detect_location_osm_version_change command"
        fetch_and_save_data_from_openstreetmap(location, existing_osm_response=response)
        self.stdout.write("Minor change, location updated!")
        return Status.MINOR_CHANGE
