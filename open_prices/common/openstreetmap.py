import math

from django.conf import settings
from OSMPythonTools.api import Api, ApiResult
from OSMPythonTools.nominatim import Nominatim

EARTH_RADIUS_KM = 6371.0
LOCATION_MAJOR_MOVE_METERS = 100  # a move further than this counts as a "major" change

OSM_FIELDS_FROM_NOMINATIM = [
    "name",
    "display_name",
    "lat",
    "lon",
]  # + OSM_TAG_FIELDS + OSM_ADDRESS_FIELDS
OSM_FIELDS_FROM_OPENSTREETMAP = ["brand", "version", "version_date"]
OSM_TAG_FIELDS_MAPPING = {"class": "tag_key", "type": "tag_value"}
OSM_ADDRESS_FIELDS = [
    "postcode",
    "country",
    "country_code",
]  # 'city" is managed seperately
# https://wiki.openstreetmap.org/wiki/Key:place
OSM_ADDRESS_PLACE_FIELDS = ["village", "town", "city", "municipality"]

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
COUNTRIES_OVERPASS_QUERY = """
[out:json];
(
  relation["type"="boundary"]["boundary"="administrative"]["admin_level"="2"];
);
out body;
"""
COUNTRIES_JSON_PATH = (
    settings.BASE_DIR / "open_prices" / "locations" / "data" / "countries.json"
)


def get_location_from_nominatim(osm_id: int, osm_type: str) -> list:
    """
    Nominatim API.
    https://wiki.openstreetmap.org/wiki/Nominatim
    """
    client = Nominatim()
    search_query = f"{osm_type.lower()}/{osm_id}"
    return client.query(search_query, lookup=True).toJSON()


def get_location_from_osm(osm_id: int, osm_type: str, history: bool) -> ApiResult:
    """
    Main OSM API.
    https://wiki.openstreetmap.org/wiki/API_v0.6
    """
    api = Api()
    response = api.query(f"{osm_type.lower()}/{osm_id}", history=history)
    return response


def get_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in kilometers between two lat/lon points."""
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = (
        math.radians(coord) for coord in (lat1, lon1, lat2, lon2)
    )
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def get_location_dict_from_osm(
    osm_id: int, osm_type: str, existing_osm_response: ApiResult | None = None
) -> dict:
    """
    Input: OSM API response
    Output: Dictionary with a subset of location details.
    `response` can be passed in when the caller already fetched it (e.g. to
    decide whether to update a Location), to avoid querying the OSM API twice.
    """
    response = (
        get_location_from_osm(osm_id, osm_type, history=False)
        if existing_osm_response is None
        else existing_osm_response
    )
    return {
        "name": response.tag("name"),
        # "tag_key": "",  # fetched from nominatim
        # "tag_value": "",  # fetched from nominatim
        "brand": response.tag("brand"),
        "brand_wikidata": response.tag("brand:wikidata"),
        "brand_wikipedia": response.tag("brand:wikipedia"),
        "lat": response.lat(),
        "lon": response.lon(),
        "version": response.version(),
        "version_date": response.timestamp(),
        "tags": response.tags(),  # not used
    }


def get_historical_location_from_openstreetmap(
    osm_id: int, osm_type: str, historical_datetime: str
) -> ApiResult:
    """
    Loop until we find a version that is more recent than the historical_datetime  # noqa
    And return the previous version
    """
    response = get_location_from_osm(osm_id, osm_type, history=True)
    if len(response.history()) == 1:
        return response.history()[0]
    for index, location_version in enumerate(response.history()):
        if historical_datetime < location_version.timestamp():
            return response.history()[index - 1]
    return response.history()[-1]


def has_moved_significantly(location, osm_data: dict) -> bool:
    lat, lon = osm_data.get("lat"), osm_data.get("lon")
    if lat is None or lon is None:
        return False
    if location.osm_lat is None or location.osm_lon is None:
        return False
    distance_km = get_distance_km(
        float(location.osm_lat), float(location.osm_lon), lat, lon
    )
    return distance_km * 1000 > LOCATION_MAJOR_MOVE_METERS


def has_tag_changed(location, osm_data: dict) -> bool:
    """Whether the location's primary OSM tag (e.g. "shop"="supermarket") changed value, or disappeared."""
    if not location.osm_tag_key or "tag_value" not in osm_data:
        return False
    return osm_data["tag_value"] != location.osm_tag_value


def is_deleted_osm_error(exception: Exception) -> bool:
    """
    True if `exception` was raised because OSM returned 410 Gone, i.e. the
    element existed in the past but has since been deleted.
    """
    cause = exception.args[-1] if exception.args else None
    return getattr(cause, "code", None) == 410


def has_major_osm_change(location, osm_data: dict) -> bool:
    """
    A "major" change = the OSM version changed AND (the name, brand or primary
    tag changed, or the point moved by more than LOCATION_MAJOR_MOVE_METERS).

    `osm_data` is a dict with "version", "name", "brand", "lat" & "lon" keys
    (see `get_location_dict_from_osm`), plus an optional
    "tag_value" key holding the current value of the location's
    `osm_tag_key`, so this can be compared against either a live OSM
    response or a previously stored dict.
    """
    if osm_data.get("version") == location.osm_version:
        return False
    return (
        osm_data.get("name") != location.osm_name
        or osm_data.get("brand") != location.osm_brand
        or has_tag_changed(location, osm_data)
        or (location.is_osm_type_node and has_moved_significantly(location, osm_data))
    )


def get_location_dict_from_all_apis(
    location, existing_osm_response: ApiResult | None = None
):
    """
    Fetches location details from 2 APIs: Nominatim and the OSM API.
    `existing_osm_response` can be passed in when the caller already fetched it from
    the OSM API, to avoid querying it twice.
    """
    location_dict = dict()
    # first fetch data from Nominatim
    try:
        response = get_location_from_nominatim(
            osm_id=location.osm_id, osm_type=location.osm_type.lower()
        )
        if len(response):
            for osm_field in OSM_FIELDS_FROM_NOMINATIM:
                if osm_field in response[0]:
                    key = f"osm_{osm_field}"
                    value = response[0][osm_field]
                    location_dict[key] = value
            for osm_field in list(OSM_TAG_FIELDS_MAPPING.keys()):
                if osm_field in response[0]:
                    key = f"osm_{OSM_TAG_FIELDS_MAPPING[osm_field]}"
                    value = response[0][osm_field]
                    location_dict[key] = value
            if "address" in response[0]:
                for osm_address_field in OSM_ADDRESS_FIELDS:
                    if osm_address_field in response[0]["address"]:
                        key = f"osm_address_{osm_address_field}"
                        value = response[0]["address"][osm_address_field]
                        if osm_address_field == "country_code":  # "fr" -> "FR"
                            value = value.upper()
                        location_dict[key] = value
                # manage city
                location_dict["osm_address_city"] = None
                for osm_address_place_field in OSM_ADDRESS_PLACE_FIELDS:
                    if osm_address_place_field in response[0]["address"]:
                        if not location_dict["osm_address_city"]:
                            key = "osm_address_city"
                            value = response[0]["address"][osm_address_place_field]
                            location_dict[key] = value
    except Exception:
        # logger.exception("Error returned from OpenStreetMap")
        pass
    # fetch extra data from OSM
    try:
        response = get_location_dict_from_osm(
            osm_id=location.osm_id,
            osm_type=location.osm_type.lower(),
            existing_osm_response=existing_osm_response,
        )
        if response:
            for osm_field in OSM_FIELDS_FROM_OPENSTREETMAP:
                if osm_field in response:
                    key = f"osm_{osm_field}"
                    value = response[osm_field]
                    location_dict[key] = value
    except Exception:
        pass
    # return
    return location_dict
