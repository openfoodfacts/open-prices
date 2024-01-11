import logging

import sentry_sdk
from openfoodfacts import API, APIVersion, Country, Flavor
from openfoodfacts.types import JSONType
from openfoodfacts.utils import get_logger
from OSMPythonTools.nominatim import Nominatim
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings
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
OFF_FIELDS = [
    "product_name",
    "product_quantity",
    "brands",
    "image_url",
    "unique_scans_n",
]


def openfoodfacts_product_search(code: str):
    client = API(
        username=None,
        password=None,
        country=Country.world,
        flavor=Flavor.off,
        version=APIVersion.v2,
        environment=settings.environment,
    )
    return client.product.get(code)


def normalize_product_fields(product: JSONType) -> JSONType:
    """Normalize product fields and return a product dict
    ready to be inserted in the database.

    :param product: the product to normalize
    :return: the normalized product
    """
    product = product.copy()
    product_quantity = int(product.get("product_quantity") or 0)
    if product_quantity >= 100_000:
        # If the product quantity is too high, it's probably an
        # error, and cause an OutOfRangeError in the database
        product["product_quantity"] = None

    # Some products have null unique_scans_n
    if product["unique_scans_n"] is None:
        product["unique_scans_n"] = 0

    return product


def fetch_product_openfoodfacts_details(product: ProductBase) -> JSONType | None:
    product = {}
    try:
        response = openfoodfacts_product_search(code=product.code)
        if response["status"]:
            product["source"] = Flavor.off
            for off_field in OFF_FIELDS:
                if off_field in response["product"]:
                    product[off_field] = response["product"][off_field]
            product = normalize_product_fields(product)
        return product
    except Exception:
        logger.exception("Error returned from Open Food Facts")
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
