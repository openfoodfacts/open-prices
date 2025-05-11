import os
import sys
import time

from open_prices.common import openfoodfacts as common_openfoodfacts
from scripts.utils import create_price, read_csv

OPEN_PRICES_CREATE_PRICE_ENDPOINT = f'{os.environ.get("API_ENDPOINT")}/prices'
OPEN_PRICES_TOKEN = os.environ.get("API_TOKEN")

REQUIRED_ENV_PARAMS = [
    # "FILEPATH"
    # "DELIMITER" (optional)
    "PRODUCT_CODE_FIELD",
    "PRODUCT_NAME_FIELD",
    "PRICE_FIELD",
    "CURRENCY",
    "LOCATION_OSM_ID",
    "LOCATION_OSM_TYPE",
    "DATE",
    "PROOF_ID",
    "API_ENDPOINT",
    "API_TOKEN",
    # DRY_RUN
]


def map_gdpr_price_list_to_open_prices(price_list, extra_data={}):
    # map source fields to op fields
    open_prices_price_list = list()
    for price in price_list:
        open_prices_price = dict()
        # product_name
        if os.environ.get("PRODUCT_NAME_FIELD"):
            open_prices_price["product_name"] = price.get(
                os.environ.get("PRODUCT_NAME_FIELD")
            )
        # product_code
        open_prices_price["product_code"] = price.get(
            os.environ.get("PRODUCT_CODE_FIELD")
        )
        # price
        price_str = price.get(os.environ.get("PRICE_FIELD"))
        open_prices_price["price"] = (
            float(price_str.replace(",", ".")) if price_str else None
        )
        # print(open_prices_price)
        open_prices_price_list.append({**open_prices_price, **extra_data})

    return open_prices_price_list


def filter_rules(op_price_list):
    """
    Rules to skip some prices (on code, name...)
    """
    op_price_list_filtered = list()

    for op_price in op_price_list:
        passes_test = True

        if not op_price["product_code"]:
            passes_test = False
        elif not common_openfoodfacts.barcode_is_valid(op_price["product_code"]):
            passes_test = False

        if not op_price["price"]:
            passes_test = False

        if passes_test:
            op_price_list_filtered.append(op_price)

    return op_price_list_filtered


if __name__ == "__main__":
    """
    How-to run:
    > FILEPATH= poetry run python scripts/shop_import/create_prices_from_csv.py
    Required params: see REQUIRED_ENV_PARAMS
    """
    # Step 1: read input file
    if not os.environ.get("FILEPATH"):
        sys.exit("Error: missing FILEPATH env")
    filepath = os.environ.get("FILEPATH")
    print(f"===== Reading {filepath}")
    if os.environ.get("DELIMITER"):
        price_list = read_csv(filepath, delimiter=os.environ.get("DELIMITER"))
    else:
        price_list = read_csv(filepath)
    print(len(price_list))

    print("===== Input example:")
    print(price_list[0])

    # Step 2: check env params are all present
    print("===== Checking env params")
    for env_param in REQUIRED_ENV_PARAMS:
        if not os.environ.get(env_param):
            sys.exit(f"Error: missing {env_param} env")
    print("All good :)")

    # Step 3: transform input into OP format
    print("===== Mapping source file to Open Prices format")
    source = os.environ.get("SOURCE")
    extra_data = {
        "currency": os.environ.get("CURRENCY"),
        "location_osm_id": int(os.environ.get("LOCATION_OSM_ID")),
        "location_osm_type": os.environ.get("LOCATION_OSM_TYPE"),
        "date": os.environ.get("DATE"),
        # proof_id must be of type "SHOP_IMPORT" :)
        "proof_id": int(os.environ.get("PROOF_ID")),
    }
    open_prices_price_list = map_gdpr_price_list_to_open_prices(
        price_list, extra_data=extra_data
    )
    print(len(open_prices_price_list))

    # Step 4: filter prices depending on specific rules
    print("===== Applying source filtering rules")
    open_prices_price_list_filtered = filter_rules(open_prices_price_list)
    print(len(open_prices_price_list_filtered))

    print("===== Output example (extra fields will be ignored)")
    print(open_prices_price_list_filtered[0])

    # Step 5: send prices to backend via API
    if os.environ.get("DRY_RUN") == "False":
        print(f"===== Uploading data to {os.environ.get('API_ENDPOINT')}")
        progress = 0
        for index, price in enumerate(open_prices_price_list_filtered):
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
        sys.exit("===== No prices uploaded (DRY_RUN env missing or set to 'True')")
