from OSMPythonTools.api import Api
from OSMPythonTools.nominatim import Nominatim

OSM_FIELDS_FROM_NOMINATIM = ["name", "display_name", "lat", "lon"]
OSM_FIELDS_FROM_OPENSTREETMAP = ["brand", "version"]
OSM_TAG_FIELDS_MAPPING = {"class": "tag_key", "type": "tag_value"}
OSM_ADDRESS_FIELDS = [
    "postcode",
    "country",
    "country_code",
]  # 'city" is managed seperately
# https://wiki.openstreetmap.org/wiki/Key:place
OSM_ADDRESS_PLACE_FIELDS = ["village", "town", "city", "municipality"]


def get_location_from_nominatim(osm_id: int, osm_type: str) -> list:
    client = Nominatim()
    search_query = f"{osm_type.lower()}/{osm_id}"
    return client.query(search_query, lookup=True).toJSON()


def get_location_from_openstreetmap(osm_id: int, osm_type: str) -> dict:
    api = Api()
    response = api.query(f"{osm_type.lower()}/{osm_id}")
    return {
        "name": response.tag("name"),
        # "tag_key": "",
        # "tag_value": "",
        "brand": response.tag("brand"),
        "brand_wikidata": response.tag("brand:wikidata"),
        "brand_wikipedia": response.tag("brand:wikipedia"),
        "lat": response.lat(),
        "lon": response.lon(),
        "version": response.version(),
    }


def get_location_dict(location):
    location_dict = dict()
    # fetch data from Nominatim
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
    # fetch extra data from OpenStreetMap
    try:
        response = get_location_from_openstreetmap(
            osm_id=location.osm_id, osm_type=location.osm_type.lower()
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
