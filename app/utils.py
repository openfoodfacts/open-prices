import logging

import sentry_sdk
from openfoodfacts import API, APIVersion, Country, Environment, Flavor
from openfoodfacts.utils import get_logger
from OSMPythonTools.nominatim import Nominatim
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.schemas import LocationBase, ProductBase

logger = get_logger(__name__)


# Sentry
# ------------------------------------------------------------------------------
def init_sentry(sentry_dsn: str | None, integrations: list[Integration] | None = None):
    if sentry_dsn:
        integrations = integrations or []
        integrations.append(
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.WARNING,  # Send warning and errors as events
            ),
        )
        sentry_sdk.init(  # type:ignore  # mypy say it's abstract
            sentry_dsn,
            integrations=integrations,
        )


# OpenFoodFacts
# ------------------------------------------------------------------------------
OFF_FIELDS = ["product_name", "product_quantity", "brands", "image_url"]


def openfoodfacts_product_search(code: str):
    client = API(
        username=None,
        password=None,
        country=Country.world,
        flavor=Flavor.off,
        version=APIVersion.v2,
        environment=Environment.org,
    )
    return client.product.get(code)


def fetch_product_openfoodfacts_details(product: ProductBase):
    product_openfoodfacts_details = dict()
    try:
        response = openfoodfacts_product_search(code=product.code)
        if response["status"]:
            product_openfoodfacts_details["source"] = Flavor.off
            for off_field in OFF_FIELDS:
                if off_field in response["product"]:
                    product_openfoodfacts_details[off_field] = response["product"][
                        off_field
                    ]
        return product_openfoodfacts_details
    except Exception:
        logger.exception("Error returned from OpenFoodFacts")
        return


# OpenStreetMap
# ------------------------------------------------------------------------------
OSM_FIELDS = ["name", "display_name", "lat", "lon"]
OSM_ADDRESS_FIELDS = ["postcode", "country"]  # 'city" is managed seperately
# https://wiki.openstreetmap.org/wiki/Key:place
OSM_ADDRESS_PLACE_FIELDS = ["village", "town", "city", "municipality"]


def openstreetmap_nominatim_search(osm_id: int, osm_type: str):
    client = Nominatim()
    search_query = f"{osm_type}/{osm_id}"
    return client.query(search_query, lookup=True).toJSON()


def fetch_location_openstreetmap_details(location: LocationBase):
    location_openstreetmap_details = dict()
    try:
        response = openstreetmap_nominatim_search(
            osm_id=location.osm_id, osm_type=location.osm_type.value.lower()
        )
        if len(response):
            for osm_field in OSM_FIELDS:
                if osm_field in response[0]:
                    location_openstreetmap_details[f"osm_{osm_field}"] = response[0][
                        osm_field
                    ]
            if "address" in response[0]:
                for osm_address_field in OSM_ADDRESS_FIELDS:
                    if osm_address_field in response[0]["address"]:
                        location_openstreetmap_details[
                            f"osm_address_{osm_address_field}"
                        ] = response[0]["address"][osm_address_field]
                # manage city
                location_openstreetmap_details["osm_address_city"] = None
                for osm_address_place_field in OSM_ADDRESS_PLACE_FIELDS:
                    if osm_address_place_field in response[0]["address"]:
                        if not location_openstreetmap_details["osm_address_city"]:
                            location_openstreetmap_details[
                                "osm_address_city"
                            ] = response[0]["address"][osm_address_place_field]

        return location_openstreetmap_details
    except Exception:
        logger.exception("Error returned from OpenStreetMap")
        return
