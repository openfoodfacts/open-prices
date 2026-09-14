from OSMPythonTools.api import ApiResult

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations.models import Location


def fetch_and_save_data_from_openstreetmap(
    location: Location, existing_osm_response: ApiResult | None = None
):
    """
    `existing_osm_response` can be passed in when the caller already fetched it from
    the OSM API, to avoid querying it twice.
    """
    location_openstreetmap_details = (
        common_openstreetmap.get_location_dict_from_all_apis(
            location, existing_osm_response=existing_osm_response
        )
    )
    if location_openstreetmap_details:
        for key, value in location_openstreetmap_details.items():
            setattr(location, key, value)
        location.save()
