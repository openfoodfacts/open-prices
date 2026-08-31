from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


def fetch_and_save_data_from_openstreetmap(location: Location):
    location_openstreetmap_details = common_openstreetmap.get_location_dict(location)
    if location_openstreetmap_details:
        new_version = location_openstreetmap_details.get("osm_version")
        new_name = location_openstreetmap_details.get("osm_name")
        new_brand = location_openstreetmap_details.get("osm_brand")
        # detect meaningful changes: version changed + name or brand changed
        version_changed = new_version and new_version != location.osm_version
        identity_changed = (
            new_name != location.osm_name or new_brand != location.osm_brand
        )
        if version_changed and identity_changed:
            # create a new Location record for the new brand/version
            osm_fields = {
                k: v
                for k, v in location_openstreetmap_details.items()
                if k in Location.TYPE_OSM_OPTIONAL_FIELDS
            }
            Location.objects.create(
                type=location.type,
                osm_id=location.osm_id,
                osm_type=location.osm_type,
                **osm_fields,
            )
        else:
            # no meaningful change - update existing record in place
            for key, value in location_openstreetmap_details.items():
                setattr(location, key, value)
            location.save()
