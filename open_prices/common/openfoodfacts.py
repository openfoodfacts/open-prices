import datetime

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
from openfoodfacts.types import JSONType

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
            environment=Environment[settings.OFF_ENVIRONMENT],
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
        environment=Environment[settings.OFF_ENVIRONMENT],
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
