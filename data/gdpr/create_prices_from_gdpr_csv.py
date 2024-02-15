import csv
import os
import sys
import time

import requests

OPEN_PRICES_CREATE_PRICE_ENDPOINT = f'{os.environ.get("API_ENDPOINT")}/prices'
OPEN_PRICES_TOKEN = os.environ.get("API_TOKEN")
GDPR_FIELD_MAPPING_FILEPATH = "data/gdpr/gdpr_field_mapping.csv"

DEFAULT_PRICE_CURRENCY = "EUR"
PRICE_FIELDS = [
    "product_code",
    "product_name",
    "price",
    "currency",
    "location_osm_id",
    "location_osm_type",
    "date",
]

REQUIRED_ENV_PARAMS = [
    # "FILEPATH"
    "API_TOKEN",
    "API_ENDPOINT",
    "SOURCE",
    "LOCATION_OSM_ID",
    "LOCATION_OSM_TYPE",
    "PROOF_ID",
    # DRY_MODE
]


def gdpr_source_cleanup_rules(gdpr_source, op_field, gdpr_field_name, gdpr_field_value):
    if gdpr_source == "CARREFOUR":
        # input: |3178050000749|
        # output: 3178050000749
        if op_field == "product_code":
            gdpr_field_value = gdpr_field_value.replace("|", "")
        # input: 27/05/2021
        # output: 2021-05-27
        elif op_field == "date":
            # TODO
            gdpr_field_value = gdpr_field_value
    elif gdpr_source == "AUCHAN":
        if op_field == "price":
            gdpr_field_value = float(gdpr_field_value.replace(",", "."))
    return gdpr_field_value


def gdpr_source_filter_rules(op_price_list, gdpr_source=""):
    op_price_list_filtered = list()

    for op_price in op_price_list:
        passes_test = True
        if gdpr_source == "CARREFOUR":
            pass
        elif gdpr_source == "AUCHAN":
            if len(op_price["product_code"]) < 13:
                passes_test = False
            elif op_price["product_code"].endswith("000000"):
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
    open_prices_price_list = list()

    # get mapping file
    gdpr_field_mapping = read_gdpr_field_mapping_csv()

    # map source fields to op fields
    for gdpr_price in gdpr_price_list:
        open_prices_price = dict()
        for field_mapping in gdpr_field_mapping:
            op_field = field_mapping["OPEN_PRICES_FIELD"]
            if op_field in PRICE_FIELDS:
                gdpr_field_name = field_mapping[f"{gdpr_source}_FIELD"]
                gdpr_field_value = gdpr_price[gdpr_field_name]
                gdpr_price_field_cleaned = gdpr_source_cleanup_rules(
                    gdpr_source, op_field, gdpr_field_name, gdpr_field_value
                )
                open_prices_price[op_field] = gdpr_price_field_cleaned
        # print(open_prices_price)
        open_prices_price_list.append({**open_prices_price, **extra_data})

    return open_prices_price_list


def create_price(price):
    headers = {"Authorization": f"Bearer {OPEN_PRICES_TOKEN}"}
    response = requests.post(
        OPEN_PRICES_CREATE_PRICE_ENDPOINT, json=price, headers=headers
    )
    print(response.content)
    if response.status_code == 201:
        print("Price created !")


if __name__ == "__main__":
    """
    How-to run:
    > FILEPATH= poetry run python data/gdpr/create_prices_from_gdpr_csv.py
    Required params: see REQUIRED_ENV_PARAMS
    """
    filepath = os.environ.get("FILEPATH")
    print(f"Reading {filepath}")
    gdpr_price_list = read_gdpr_csv(filepath)
    print(len(gdpr_price_list))
    print(gdpr_price_list[0])

    print("Checking env params")
    for env_param in REQUIRED_ENV_PARAMS:
        if not os.environ.get(env_param):
            sys.exit(f"Error: missing {env_param} env")

    print("Mapping source file to Open Prices format")
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
    print(open_prices_price_list[0])

    print("Applying filtering rules")
    open_prices_price_list_filtered = gdpr_source_filter_rules(
        open_prices_price_list, gdpr_source=source
    )
    print(len(open_prices_price_list_filtered))
    print(open_prices_price_list_filtered[0])

    if os.environ.get("DRY_MODE") == "True":
        print(f"Uploading data to {OPEN_PRICES_CREATE_PRICE_ENDPOINT}")
        progress = 0
        for index, price in enumerate(open_prices_price_list_filtered[:100]):
            create_price(price)
            # some pauses to be safe
            progress += 1
            if (progress % 10) == 0:
                time.sleep(1)
            if (progress % 50) == 0:
                print(f"{progress}/{len(open_prices_price_list_filtered)}...")
    else:
        sys.exit("No prices uploaded (DRY_MODE env missing or set to 'False')")
