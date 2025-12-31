import os
import sys
import time

from openfoodfacts.barcode import normalize_barcode

from open_prices.common import openfoodfacts as common_openfoodfacts
from scripts.utils import create_price, is_valid_date, read_csv, read_json

OPEN_PRICES_CREATE_PRICE_ENDPOINT = f'{os.environ.get("API_ENDPOINT")}/prices'
OPEN_PRICES_TOKEN = os.environ.get("API_TOKEN")

REQUIRED_ENV_PARAMS = [
    "FILEPATH",  # path to CSV file
    # "DELIMITER",  # optional
    "MAPPING_FILEPATH",
    "DATE",  # expected format: YYYY-MM-DD
    "PROOF_ID",  # must be of type 'SHOP_IMPORT' :)
    "API_ENDPOINT",
    "API_TOKEN",  # will be different if .net or .org
    # DRY_RUN  # optional, set to 'False' to upload
]


def _get_field_from_shop_mapping_fields(
    shop_price, shop_mapping_fields, open_prices_field
):
    field_mapping = next(
        (f for f in shop_mapping_fields if f["open_prices"] == open_prices_field),
        None,
    )
    if field_mapping:
        return shop_price.get(field_mapping["shop"])
    return None


def shop_filter_rules(shop_price_list, shop_mapping_filters):
    """
    Rules to skip some prices (on code, name...)
    """
    shop_price_list_filtered = list()

    for shop_price in shop_price_list:
        passes_test = True

        for filter in shop_mapping_filters:
            shop_field_value = shop_price.get(filter["shop"])
            if not shop_field_value or not eval(
                f"'{shop_field_value}' {filter['sign']} '{filter['value']}'"
            ):
                passes_test = False

        if passes_test:
            shop_price_list_filtered.append(shop_price)

    return shop_price_list_filtered


def map_shop_price_list_to_open_prices(
    shop_price_list, shop_mapping, shop_mapping_fields
):
    """
    Map a price list from Shop format to Open Prices format
    - some fields are fetched from shop_mapping: currency, location_osm_id, location_osm_type
    - some fields are expected from shop_mapping_fields: product_name, product_code, price
    - some fields are set from env: date, proof_id
    """
    open_prices_price_list = list()

    for shop_price in shop_price_list:
        open_prices_price = dict()
        # product_name
        open_prices_price["product_name"] = _get_field_from_shop_mapping_fields(
            shop_price, shop_mapping_fields, "product_name"
        )
        # product_code (with cleanup)
        open_prices_price["product_code"] = _get_field_from_shop_mapping_fields(
            shop_price, shop_mapping_fields, "product_code"
        )
        if open_prices_price["product_code"]:
            open_prices_price["product_code"] = normalize_barcode(
                open_prices_price["product_code"].strip()
            )
        # price (with cleanup)
        open_prices_price["price"] = _get_field_from_shop_mapping_fields(
            shop_price, shop_mapping_fields, "price"
        )
        if open_prices_price["price"]:
            open_prices_price["price"] = open_prices_price["price"].replace(",", ".")
        # currency
        open_prices_price["currency"] = shop_mapping.get("shop_currency")
        # location
        open_prices_price["location_osm_id"] = shop_mapping.get("shop_location_osm_id")
        open_prices_price["location_osm_type"] = shop_mapping.get(
            "shop_location_osm_type"
        )
        # date
        open_prices_price["date"] = os.environ.get("DATE")
        # proof_id
        open_prices_price["proof_id"] = os.environ.get("PROOF_ID")
        # print(open_prices_price)
        open_prices_price_list.append(open_prices_price)

    return open_prices_price_list


def open_prices_filter_rules(open_prices_price_list):
    """
    Rules to skip some prices (on code, name...)
    """
    open_prices_price_list_filtered = list()

    for open_prices_price in open_prices_price_list:
        passes_test = True

        # product_code is mandatory and must be valid
        if not open_prices_price["product_code"]:
            passes_test = False
        elif not common_openfoodfacts.barcode_is_valid(
            open_prices_price["product_code"]
        ):
            passes_test = False

        # price is mandatory
        if not open_prices_price["price"]:
            passes_test = False

        if passes_test:
            open_prices_price_list_filtered.append(open_prices_price)

    return open_prices_price_list_filtered


if __name__ == "__main__":
    """
    How-to run: see README.md
    Required params: see REQUIRED_ENV_PARAMS
    """
    print("===== Step 1/7: Checking env params")
    for env_param in REQUIRED_ENV_PARAMS:
        if not os.environ.get(env_param):
            sys.exit(f"Error: missing {env_param} env")
        if env_param == "DATE":
            if not is_valid_date(os.environ.get("DATE")):
                sys.exit("Error: DATE env not valid (expected format: YYYY-MM-DD)")
    print("All good :)")

    filepath = os.environ.get("FILEPATH")
    print(f"===== Step 2/7: Reading {filepath}")
    if os.environ.get("DELIMITER"):
        shop_price_list = read_csv(filepath, delimiter=os.environ.get("DELIMITER"))
    else:
        shop_price_list = read_csv(filepath)
    print(len(shop_price_list))

    print(">>>>> Input example:")
    print(shop_price_list[0])

    shop_mapping_filepath = os.environ.get("MAPPING_FILEPATH")
    print(f"===== Step 3/7: Reading {shop_mapping_filepath}")
    shop_mapping = read_json(shop_mapping_filepath)
    shop_mapping_fields = shop_mapping.get("fields", [])
    shop_mapping_filters = shop_mapping.get("filters", [])
    print(f"Found {len(shop_mapping_fields)} field mappings")
    print(f"Found {len(shop_mapping_filters)} shop filters")

    print("===== Step 4/7: Applying shop filtering rules")
    shop_price_list_filtered = shop_filter_rules(shop_price_list, shop_mapping_filters)
    print(len(shop_price_list_filtered))

    print("===== Step 5/7: Mapping source file to Open Prices format")
    open_prices_price_list = map_shop_price_list_to_open_prices(
        shop_price_list_filtered, shop_mapping, shop_mapping_fields
    )
    print(len(open_prices_price_list))

    print("===== Step 6/7: Applying open_prices filtering rules")
    open_prices_price_list_filtered = open_prices_filter_rules(open_prices_price_list)
    print(len(open_prices_price_list_filtered))

    print(">>>>> Output example (extra fields will be ignored)")
    print(open_prices_price_list_filtered[0])

    if os.environ.get("DRY_RUN") == "False":
        print(f"===== Step 7/7: Uploading data to {os.environ.get('API_ENDPOINT')}")
        progress = 0
        for _index, price in enumerate(open_prices_price_list_filtered):
            create_price(
                price, os.environ.get("API_ENDPOINT"), os.environ.get("API_TOKEN")
            )
            # some pauses to be safe
            progress += 1
            if (progress % 10) == 0:
                time.sleep(1)
            if (progress % 50) == 0:
                print(f"{progress}/{len(open_prices_price_list_filtered)}...")
    else:
        sys.exit(
            "===== Step 7/7: No prices uploaded (DRY_RUN env missing or set to 'True')"
        )
