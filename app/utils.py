import logging

import sentry_sdk
from openfoodfacts import API, APIVersion, Country, Flavor
from openfoodfacts.images import generate_image_url
from openfoodfacts.types import JSONType
from openfoodfacts.utils import get_logger
from OSMPythonTools.nominatim import Nominatim
from sentry_sdk.integrations import Integration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings
from app.schemas import LocationFull, ProductFull

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
    "product_quantity_unit",
    "categories_tags",
    "brands",
    "brands_tags",
    "labels_tags",
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

    for key in ("categories_tags", "labels_tags", "brands_tags"):
        if key in product and product[key] is None:
            # Set the field to an empty list if it's None
            product[key] = []

    return product


def generate_openfoodfacts_main_image_url(
    code: str, images: JSONType, lang: str
) -> str | None:
    """Generate the URL of the main image of a product.

    :param code: The code of the product
    :param images: The images of the product
    :param lang: The main language of the product
    :return: The URL of the main image of the product or None if no image is
      available.
    """
    image_key = None
    if f"front_{lang}" in images:
        image_key = f"front_{lang}"
    else:
        for key in (k for k in images if k.startswith("front_")):
            image_key = key
            break

    if image_key:
        image_rev = images[image_key]["rev"]
        image_id = f"{image_key}.{image_rev}.400"
        return generate_image_url(
            code, image_id=image_id, flavor=Flavor.off, environment=settings.environment
        )

    return None


def fetch_product_openfoodfacts_details(product: ProductFull) -> JSONType | None:
    product_dict = {}
    try:
        response = openfoodfacts_product_search(code=product.code)
        if response["status"]:
            product_dict["source"] = Flavor.off
            for off_field in OFF_FIELDS:
                if off_field in response["product"]:
                    product_dict[off_field] = response["product"][off_field]
            product_dict = normalize_product_fields(product_dict)
        return product_dict
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


def fetch_location_openstreetmap_details(location: LocationFull):
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
