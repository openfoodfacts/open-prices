import datetime
import functools
import re

import openfoodfacts
import requests
import tqdm
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from openfoodfacts import (
    API,
    APIVersion,
    Country,
    DatasetType,
    Environment,
    Flavor,
    ProductDataset,
)
from openfoodfacts.images import generate_image_url
from openfoodfacts.taxonomy import (
    create_taxonomy_mapping,
    get_taxonomy,
    map_to_canonical_id,
)
from openfoodfacts.types import COUNTRY_CODE_TO_NAME, JSONType

OFF_CREATE_FIELDS = [
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
OFF_UPDATE_FIELDS = OFF_CREATE_FIELDS + ["source", "source_last_synced"]


# Taxonomy mapping generation takes ~200ms, so we cache it to avoid
# recomputing it for each request.
_cached_create_taxonomy_mapping = functools.lru_cache()(create_taxonomy_mapping)
# Also cache the get_taxonomy function to avoid reading from disk at each
# request.
_cached_get_taxonomy = functools.lru_cache()(get_taxonomy)


def normalize_taxonomized_tags(taxonomy_type: str, value_tags: list[str]) -> list[str]:
    """Normalizes a list of tags based on the taxonomy type.

    :param taxonomy_type: The type of taxonomy ('category', 'label', or
        'origin').
    :param value_tags: A list of tag values to normalize (e.g.,
        ["fr: Boissons"]).
    :raises RuntimeError: If the taxonomy type is not one of 'category',
        'label', or 'origin'
    :raises ValueError: If the value_tag could not be mapped to a canonical ID.
    :return: The normalized tags (e.g., ["en:beverages"]). The order of the
        tags is the same as the input list.
    """
    if taxonomy_type not in ("category", "label", "origin"):
        raise RuntimeError(
            f"Invalid taxonomy type: {taxonomy_type}. Expected one of 'category', 'label', or 'origin'."
        )

    # Use the cached version of the get_taxonomy function to avoid
    # creating it multiple times.
    category_taxonomy = _cached_get_taxonomy(taxonomy_type)
    # the tag (category or label tag) can be provided by the mobile app in any
    # language, with language prefix (ex: `fr: Boissons`).
    # We need to map it to the canonical id (ex: `en:beverages`) to store it
    # in the database.
    # The `map_to_canonical_id` function maps the value (ex:
    # `fr: Boissons`) to the canonical id (ex: `en:beverages`).
    # We use the cached version of this function to avoid
    # creating it multiple times.
    # If the entry does not exist in the taxonomy, the tag will
    # be set to the tag version of the value (ex: `fr:boissons`).
    taxonomy_mapping = _cached_create_taxonomy_mapping(category_taxonomy)
    mapped_tags = map_to_canonical_id(taxonomy_mapping, value_tags)
    # Keep the order of the tags as they were provided
    return [mapped_tags[k] for k in mapped_tags]


def authenticate(username, password):
    """
    Request: POST with form data
    Response:
    - 200: {"status":1,"status_verbose":"user signed-in","user":{"admin":0,"cc":"fr","country":"en:france","moderator":1,"name":"Prenom","preferred_language":"fr"},"user_id":"username"}  # noqa
    - 403: {"status": 0,"status_verbose": "user not signed-in"}
    """
    data = {"user_id": username, "password": password, "body": 1}
    return requests.post(f"{settings.OAUTH2_SERVER_URL}", data=data)


def build_product_dict(product: JSONType, flavor) -> JSONType:
    # Step 1: init
    product_dict = dict()
    product_dict["source"] = flavor
    product_dict["source_last_synced"] = timezone.now()

    # Step 2: build the product dict
    for off_field in OFF_CREATE_FIELDS:
        if off_field in product:
            product_dict[off_field] = product[off_field]

    # Step 3: cleanup
    # fix product_quantity
    product_quantity = int(product_dict.get("product_quantity") or 0)
    if product_quantity >= 100_000:
        # If the product quantity is too high, it's probably an
        # error, and may cause an OutOfRangeError in the database
        product_dict["product_quantity"] = None
    # fix unique_scans_n (avoid null value)
    if not product_dict.get("unique_scans_n"):
        product_dict["unique_scans_n"] = 0

    return product_dict


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
            code,
            image_id=image_id,
            flavor=flavor,
            environment=Environment[settings.ENVIRONMENT],
        )

    return None


def get_product(code: str, flavor: Flavor = Flavor.off) -> JSONType | None:
    client = API(
        user_agent=settings.OFF_USER_AGENT,
        username=None,
        password=None,
        country=Country.world,
        flavor=flavor,
        version=APIVersion.v2,
        environment=Environment[settings.ENVIRONMENT],
    )
    return client.product.get(code)


def get_product_dict(code: str, flavor=Flavor.off) -> JSONType | None:
    product_dict = dict()
    try:
        response = get_product(code=code, flavor=flavor)
        if response:
            product_dict = build_product_dict(response, flavor)
        return product_dict
    except Exception:
        # logger.exception("Error returned from Open Food Facts")
        return None


def import_product_db(
    flavor: Flavor = Flavor.off, obsolete: bool = False, batch_size: int = 1000
) -> None:
    """Import from DB JSONL dump to create/update product table.

    :param db: the session to use
    :param batch_size: the number of products to create/update in a single
      transaction, defaults to 1000
    """
    from open_prices.products.models import Product

    print((f"Launching import_product_db (flavor={flavor}, obsolete={obsolete})"))
    existing_product_codes = set(Product.objects.values_list("code", flat=True))
    existing_product_flavor_codes = set(
        Product.objects.filter(source=flavor).values_list("code", flat=True)
    )
    print(
        f"Number of existing Product codes (from {flavor}): {len(existing_product_flavor_codes)}"
    )
    dataset = ProductDataset(
        flavor=flavor,
        dataset_type=DatasetType.jsonl,
        force_download=True,
        download_newer=True,
        obsolete=obsolete,
    )

    seen_codes = set()
    products_to_create = list()
    products_to_update = list()
    added_count = 0
    updated_count = 0
    # the dataset was created after the start of the day, every product updated
    # after should be skipped, as we don't know the exact creation time of the
    # dump
    start_datetime = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        hour=0, minute=0, second=0
    )

    for product in tqdm.tqdm(dataset):
        # Skip products without a code, or with wrong code
        if ("code" not in product) or (not product["code"].isdigit()):
            continue
        product_code = product["code"]

        # Skip duplicate products
        if product_code in seen_codes:
            continue
        seen_codes.add(product_code)

        # Some products have no "lang" field (especially non-OFF products)
        product_lang = product.get("lang", product.get("lc", "en"))
        # Store images & last_modified_t
        product_images: JSONType = product.get("images", {})
        product_last_modified_t = product.get("last_modified_t")

        # Convert last_modified_t to a datetime object
        # (sometimes the field is a string, convert to int first)
        if isinstance(product_last_modified_t, str):
            product_last_modified_t = int(product_last_modified_t)
        product_source_last_modified = (
            datetime.datetime.fromtimestamp(
                product_last_modified_t, tz=datetime.timezone.utc
            )
            if product_last_modified_t
            else None
        )
        # Skip products that have no last_modified date
        if product_source_last_modified is None:
            continue

        # Skip products that have been modified today (more recent updates are
        # possible)
        if product_source_last_modified >= start_datetime:
            print(f"Skipping {product_code}")
            continue

        # Build product dict to create/update
        product_dict = build_product_dict(product, flavor)
        product_dict["image_url"] = generate_main_image_url(
            product_code, product_images, product_lang, flavor=flavor
        )

        # Case 1: new OFF product (not in OP database)
        if product_code not in existing_product_codes:
            product_dict["code"] = product_code
            products_to_create.append(Product(**product_dict))
            existing_product_codes.add(product_code)
            added_count += 1

        # Case 2: existing product (already in OP database)
        else:
            # Update the product if it:
            # - is part of the current flavor sync (or if it has no source (created in Open Prices before OFF))  # noqa
            # - has been updated since the last sync
            existing_product_qs = (
                Product.objects.filter(code=product_code)
                .filter(Q(source=flavor) | Q(source=None))
                .filter(
                    Q(source_last_synced__lt=product_source_last_modified)
                    | Q(source_last_synced=None)
                )
            )
            if existing_product_qs.exists():
                if existing_product_qs.count() == 1:
                    products_to_update.append(
                        Product(
                            **{"id": existing_product_qs.first().id}, **product_dict
                        )
                    )
                updated_count += 1

        # update the database regularly
        products_to_create_or_update = products_to_create + products_to_update
        if (
            len(products_to_create_or_update)
            and len(products_to_create_or_update) % batch_size == 0
        ):
            Product.objects.bulk_create(
                products_to_create,
                update_conflicts=True,
                update_fields=OFF_CREATE_FIELDS,
                unique_fields=["code"],
            )
            Product.objects.bulk_update(
                products_to_update,
                fields=OFF_UPDATE_FIELDS,
            )
            print(f"Products: {added_count} added, {updated_count} updated")
            products_to_create = list()
            products_to_update = list()

    # final database update
    Product.objects.bulk_create(
        products_to_create,
        update_conflicts=True,
        update_fields=OFF_CREATE_FIELDS,
        unique_fields=["code"],
    )
    Product.objects.bulk_update(
        products_to_update,
        fields=OFF_UPDATE_FIELDS,
    )
    print(f"Products: {added_count} added, {updated_count} updated. Done!")


def barcode_is_valid(barcode: str) -> bool:
    return (
        barcode.isnumeric()
        and len(barcode) >= 6
        and openfoodfacts.barcode.has_valid_check_digit(barcode)
    )


def barcode_fix_short_codes_from_usa(barcode: str) -> str:
    """
    Fix short barcodes from USA

    10 or 11 digits: pad them to 12 digits and calculate their check digit
    12 digits: add a leading zero

    This function is based on the fact that most of the short barcodes are from
    the USA, and that they can be converted to a valid EAN-13 barcode by
    padding them with zeros to the left, and adding a leading zero.

    :param barcode: the barcode to fix
    :return: the 13-digit fixed and valid barcode, or the original barcode if
    it cannot be fixed
    """
    if len(barcode) in (10, 11, 12):
        barcode_temp = barcode.zfill(12)
        barcode_check_digit = openfoodfacts.barcode.calculate_check_digit(barcode + "0")
        barcode_temp = barcode_temp + barcode_check_digit
        if barcode_is_valid(barcode_temp):
            return barcode_temp
    elif len(barcode) == 12:
        barcode_temp = "0" + barcode
        if barcode_is_valid(barcode_temp):
            return barcode_temp
    return barcode


def country_code_to_Country(country_code: str) -> Country:
    try:
        return Country[country_code]
    except KeyError:
        return Country.world


def create_or_update_product_in_off(
    code: str,
    flavor: str = Flavor.off,
    country_code: str = "en",
    owner: str = None,
    update_params: dict = {},
) -> JSONType | None:
    client = API(
        username=settings.OFF_DEFAULT_USER,
        password=settings.OFF_DEFAULT_PASSWORD,
        user_agent=settings.OFF_USER_AGENT,
        country=country_code_to_Country(country_code),
        flavor=flavor,
        version=APIVersion.v2,
        environment=Environment[settings.ENVIRONMENT],
    )
    countries = update_params.get("countries")
    if countries:
        countries_list = countries.split(",")
        taxonomized_countries_list = [
            COUNTRY_CODE_TO_NAME[country_code_to_Country(country_code)]
            for country_code in countries_list
        ]
        update_params["countries"] = ",".join(taxonomized_countries_list)
    if owner:
        comment = f"[Open Prices, user: {owner}]"
    else:
        comment = "[Open Prices]"
    return client.product.update({"code": code, "comment": comment, **update_params})


def upload_product_image_in_off(
    code: str,
    flavor: str = Flavor.off,
    country_code: str = "en",
    image_data_base64: str = None,
    selected: JSONType | None = None,
) -> JSONType | None:
    client = API(
        user_agent=settings.OFF_USER_AGENT,
        username=settings.OFF_DEFAULT_USER,
        password=settings.OFF_DEFAULT_PASSWORD,
        country=country_code_to_Country(country_code),
        flavor=flavor,
        version=APIVersion.v3,
        environment=Environment[settings.ENVIRONMENT],
    )
    return client.product.upload_image(
        code, image_data_base64=image_data_base64, selected=selected
    )


def get_smoothie_app_version(source: str | None) -> tuple[int | None, int | None]:
    """
    Return the Smoothie app version

    Input: "Smoothie - OpenFoodFacts (4.18.1+1434)...""
    Output: (major, minor) if the request comes from Smoothie app. (None, None) otherwise.  # noqa
    """
    if source and (
        match := re.search(r"^Smoothie - OpenFoodFacts \((\d+)\.(\d+)\.(\d+)", source)
    ):
        smoothie_major = int(match.group(1))
        smoothie_minor = int(match.group(2))
        return smoothie_major, smoothie_minor

    return None, None


def is_smoothie_app_version_4_20(source: str | None) -> bool:
    """
    Return True if the requests comes from Smoothie app version 4.20.

    Why?
    - Smoothie app version 4.20 has a bug where it sets the
    `Proof.ready_for_price_tag_validation` flag to True when
    uploading price tag proofs, even when it should not be set.
    see https://github.com/openfoodfacts/smooth-app/pull/6794
    """
    smoothie_version = get_smoothie_app_version(source)
    return smoothie_version == (4, 20)


def is_smoothie_app_version_leq_4_20(source: str | None) -> bool:
    """
    Return True if the requests comes from Smoothie app version <= 4.20.

    Why?
    - Smoothie app version <= 4.20: for the proof upload request we need to
    return HTTP 200 instead of 201, if not the user's background task fails.
    see https://github.com/openfoodfacts/smooth-app/issues/6855#issuecomment-3265072440  # noqa
    """
    smoothie_version = get_smoothie_app_version(source)
    return smoothie_version[0] is not None and (smoothie_version <= (4, 20))
