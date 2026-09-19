from OSMPythonTools.api import ApiResult

from open_prices.common import openstreetmap as common_openstreetmap
from open_prices.locations import utils as location_utils
from open_prices.locations.models import Location


def fetch_and_save_data_from_openstreetmap(
    location: Location,
    existing_osm_response: ApiResult | None = None,
    save_without_historical_record: bool = False,
):
    """
    `existing_osm_response` can be passed in when the caller already fetched it from
    the OSM API, to avoid querying it twice.
    `save_without_historical_record`: set to True when this is completing a just-created, close-to-empty
    Location (e.g. right after creation from a Proof/Price) rather than a real,
    later change to an already-enriched Location - avoids a redundant 2nd history
    entry for what is really still just the initial creation. If the Location's
    history is still exactly its original "+" entry at this point (i.e. nothing
    else has touched it since creation), that entry is rewritten in place to
    reflect the enriched data, instead of leaving it showing the near-empty
    pre-enrichment state.
    """
    location_openstreetmap_details = (
        common_openstreetmap.get_location_dict_from_all_apis(
            location, existing_osm_response=existing_osm_response
        )
    )
    if location_openstreetmap_details:
        for key, value in location_openstreetmap_details.items():
            setattr(location, key, value)
        if save_without_historical_record:
            location.save_without_historical_record()
            location_utils.rewrite_creation_history_entry(
                location, location_openstreetmap_details
            )
        else:
            location.save()
