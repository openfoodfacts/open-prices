import requests
from django.conf import settings
from openfoodfacts import API, APIVersion, Country, Flavor
from openfoodfacts.images import generate_image_url
from openfoodfacts.types import JSONType

OFF_FIELDS = [
    "product_name",
    "product_quantity",
    "product_quantity_unit",
    "categories_tags",
    "brands",
    "brands_tags",
    "labels_tags",
    "image_url",
    "nutriscore_grade",
    "ecoscore_grade",
    "nova_group",
    "unique_scans_n",
]


def authenticate(username, password):
    data = {"user_id": username, "password": password, "body": 1}
    return requests.post(f"{settings.OAUTH2_SERVER_URL}", data=data)


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
        # error, and may cause an OutOfRangeError in the database
        product["product_quantity"] = None

    # Some products have null unique_scans_n
    if product.get("unique_scans_n") is None:
        product["unique_scans_n"] = 0

    for key in ("categories_tags", "labels_tags", "brands_tags"):
        if key in product and product[key] is None:
            # Set the field to an empty list if it's None
            product[key] = []

    return product


def generate_main_image_url(
    code: str, images: JSONType, lang: str, flavor: Flavor = Flavor.off
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
            code, image_id=image_id, flavor=flavor, environment=settings.environment
        )

    return None


def get_product(product_code: str, flavor: Flavor = Flavor.off) -> JSONType | None:
    client = API(
        user_agent=settings.OFF_USER_AGENT,
        username=None,
        password=None,
        country=Country.world,
        flavor=flavor,
        version=APIVersion.v2,
        environment=settings.environment,
    )
    return client.product.get(product_code)


def get_product_dict(product, flavor=Flavor.off) -> JSONType | None:
    product_dict = {}
    try:
        response = get_product(code=product.code, flavor=flavor)
        if response and response["status"]:
            product_dict["source"] = flavor
            for off_field in OFF_FIELDS:
                if off_field in response["product"]:
                    product_dict[off_field] = response["product"][off_field]
            product_dict = normalize_product_fields(product_dict)
        return product_dict
    except Exception:
        # logger.exception("Error returned from Open Food Facts")
        return None
