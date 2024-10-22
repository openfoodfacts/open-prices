import csv
import datetime
import os
import sys
import time

import requests
from utils import get_picard_product_from_subcode

OPEN_PRICES_CREATE_PRICE_ENDPOINT = f'{os.environ.get("API_ENDPOINT")}/prices'
OPEN_PRICES_TOKEN = os.environ.get("API_TOKEN")

GDPR_FIELD_MAPPING_FILEPATH = "scripts/gdpr/gdpr_field_mapping.csv"

DEFAULT_PRICE_CURRENCY = "EUR"
PRICE_FIELDS = [
    "product_code",
    "product_name",
    "price",
    "discount",  # extra
    "receipt_quantity",
    "currency",
    "location",  # extra
    "location_osm_id",
    "location_osm_type",
    "date",
]

REQUIRED_ENV_PARAMS = [
    # "FILEPATH"
    "SOURCE",
    "LOCATION",
    "LOCATION_OSM_ID",
    "LOCATION_OSM_TYPE",
    "PROOF_ID",
    "API_ENDPOINT",
    "API_TOKEN",
    # DRY_MODE
]


def gdpr_source_field_cleanup_rules(gdpr_source, op_field, gdpr_field_value):
    """
    Rules to help build the price fields
    """
    # remove any whitespace
    gdpr_field_value = gdpr_field_value.strip()

    # field-specific rules
    if op_field in ["price", "receipt_quantity"]:
        if gdpr_field_value:
            gdpr_field_value = float(gdpr_field_value.replace(",", "."))

    # shop-specific rules
    if gdpr_source == "AUCHAN":
        pass
    elif gdpr_source == "CARREFOUR":
        # input: |3178050000749|
        # output: 3178050000749
        if op_field == "product_code":
            gdpr_field_value = gdpr_field_value.replace("|", "")
        # input: 27/05/2021
        # output: 2021-05-27
        elif op_field == "date":
            gdpr_field_value = datetime.datetime.strptime(
                gdpr_field_value, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
    elif gdpr_source == "ELECLERC":
        pass
    elif gdpr_source == "INTERMARCHE":
        # input: 27/05/2021
        # output: 2021-05-27
        if op_field == "date":
            gdpr_field_value = datetime.datetime.strptime(
                gdpr_field_value, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
    elif gdpr_source == "PICARD":
        # Picard codes are a subset of the EAN codes
        # They have a length of 5 (4 if missing leading 0)
        if op_field == "product_code":
            if len(gdpr_field_value) == 4:
                gdpr_field_value = f"0{gdpr_field_value}"
        elif op_field == "date":
            gdpr_field_value = datetime.datetime.strptime(
                gdpr_field_value, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")

    return gdpr_field_value


def gdpr_source_price_cleanup_rules(gdpr_source, gdpr_op_price):
    """
    Rules to cleanup the price object
    """
    # price must be divided by receipt_quantity
    if "receipt_quantity" in gdpr_op_price:
        if gdpr_op_price["receipt_quantity"]:
            gdpr_op_price["price"] = str(
                round(gdpr_op_price["price"] / gdpr_op_price["receipt_quantity"], 2)
            )

    # discount boolean flag
    if "discount" in gdpr_op_price:
        if gdpr_op_price["discount"]:
            gdpr_op_price["price_is_discounted"] = True

    return gdpr_op_price


def gdpr_source_filter_rules(op_price_list, gdpr_source=""):
    """
    Rules to skip some prices (on code, name...)
    """
    op_price_list_filtered = list()

    for op_price in op_price_list:
        passes_test = True

        if gdpr_source == "AUCHAN":
            if (len(op_price["product_code"]) == 12) and (
                "00000" in op_price["product_code"]
            ):  # vrac
                passes_test = False
            elif (len(op_price["product_code"]) == 8) and op_price[
                "product_code"
            ].startswith(
                "900000"
            ):  # boucherie
                passes_test = False
            elif len(op_price["product_code"]) < 6:
                passes_test = False
        elif gdpr_source == "CARREFOUR":
            if "CAR" in op_price["product_code"]:
                passes_test = False
            elif op_price["product_name"] in ["BOUCHERIE", "Coupon Rem Caisse"]:
                passes_test = False
            elif op_price["discount"]:
                passes_test = False
            elif op_price["receipt_quantity"].startswith("-"):
                passes_test = False
        elif gdpr_source == "ELECLERC":
            if len(op_price["product_code"]) < 6:
                passes_test = False
            elif op_price["product_name"] in [
                "SAC KRAFT AMBIANT",
                "SAC SURGELE DRIVE + MAG",
                "REMBOURSEMENT SAC E.LECLERC",
                "SAC CAISSE GM MER",
            ]:
                passes_test = False
        elif gdpr_source == "INTERMARCHE":
            pass
        elif gdpr_source == "PICARD":
            full_product_code = get_picard_product_from_subcode(op_price)
            if full_product_code:
                op_price["product_code"] = full_product_code
            else:
                passes_test = False

        if passes_test:
            op_price_list_filtered.append(op_price)

    return op_price_list_filtered


def gdpr_source_location_rules(op_price_list):
    """
    Usually a file contains multiple locations
    To avoid errors, we ask for a location filter
    """
    op_price_list_filtered = list()

    for op_price in op_price_list:
        passes_test = True

        if op_price["location"] != os.environ.get("LOCATION"):
            passes_test = False

        if passes_test:
            op_price_list_filtered.append(op_price)

    return op_price_list_filtered


def read_gdpr_field_mapping_csv():
    with open(GDPR_FIELD_MAPPING_FILEPATH, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def read_gdpr_csv(filepath):
    price_list = list()

    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            price_list.append(row)

    return price_list


def map_gdpr_price_list_to_open_prices(gdpr_price_list, gdpr_source="", extra_data={}):
    # get mapping file
    gdpr_field_mapping = read_gdpr_field_mapping_csv()

    # map source fields to op fields
    open_prices_price_list_1 = list()
    for gdpr_price in gdpr_price_list:
        open_prices_price = dict()
        for field_mapping in gdpr_field_mapping:
            op_field = field_mapping["OPEN_PRICES_FIELD"]
            if op_field in PRICE_FIELDS:
                gdpr_field_name = field_mapping[f"{gdpr_source}_FIELD"]
                if gdpr_field_name in gdpr_price:
                    gdpr_field_value = gdpr_price[gdpr_field_name]
                    gdpr_price_field_cleaned = gdpr_source_field_cleanup_rules(
                        gdpr_source, op_field, gdpr_field_value
                    )
                    open_prices_price[op_field] = gdpr_price_field_cleaned
        # print(open_prices_price)
        open_prices_price_list_1.append({**open_prices_price, **extra_data})

    # some fields are linked together
    open_prices_price_list_2 = list()
    for gdpr_op_price in open_prices_price_list_1:
        open_prices_price_list_2.append(
            gdpr_source_price_cleanup_rules(gdpr_source, gdpr_op_price)
        )

    return open_prices_price_list_2


def create_price(price):
    headers = {"Authorization": f"Bearer {OPEN_PRICES_TOKEN}"}
    response = requests.post(
        OPEN_PRICES_CREATE_PRICE_ENDPOINT, json=price, headers=headers
    )
    if not response.status_code == 201:
        print(response.json())
        print(price)


if __name__ == "__main__":
    """
    How-to run:
    > FILEPATH= poetry run python scripts/gdpr/create_prices_from_gdpr_csv.py
    Required params: see REQUIRED_ENV_PARAMS
    """
    # Step 1: read input file
    if not os.environ.get("FILEPATH"):
        sys.exit("Error: missing FILEPATH env")
    filepath = os.environ.get("FILEPATH")
    print(f"===== Reading {filepath}")
    gdpr_price_list = read_gdpr_csv(filepath)
    print(len(gdpr_price_list))

    print("===== Input example:")
    print(gdpr_price_list[0])

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
        "currency": DEFAULT_PRICE_CURRENCY,
        "location_osm_id": int(os.environ.get("LOCATION_OSM_ID")),
        "location_osm_type": os.environ.get("LOCATION_OSM_TYPE"),
        "proof_id": int(
            os.environ.get("PROOF_ID")
        ),  # must be of type "GDPR_REQUEST" :)
    }
    open_prices_price_list = map_gdpr_price_list_to_open_prices(
        gdpr_price_list, gdpr_source=source, extra_data=extra_data
    )
    print(len(open_prices_price_list))

    # Step 4a: filter prices depending on location
    print("===== Applying location filtering rules")
    open_prices_price_list_filtered_1 = gdpr_source_location_rules(
        open_prices_price_list
    )
    print(len(open_prices_price_list_filtered_1))

    # Step 4b: filter prices depending on specific source rules
    print("===== Applying source filtering rules")
    open_prices_price_list_filtered_2 = gdpr_source_filter_rules(
        open_prices_price_list_filtered_1, gdpr_source=source
    )
    print(len(open_prices_price_list_filtered_2))

    print("===== Output example (extra fields will be ignored)")
    print(open_prices_price_list_filtered_2[0])

    # Step 5: send prices to backend via API
    if os.environ.get("DRY_RUN") == "False":
        print(f"===== Uploading data to {OPEN_PRICES_CREATE_PRICE_ENDPOINT}")
        progress = 0
        for index, price in enumerate(open_prices_price_list_filtered_2):
            create_price(price)
            # some pauses to be safe
            progress += 1
            if (progress % 10) == 0:
                time.sleep(1)
            if (progress % 50) == 0:
                print(f"{progress}/{len(open_prices_price_list_filtered_2)}...")
    else:
        sys.exit("No prices uploaded (DRY_RUN env missing or set to 'True')")
