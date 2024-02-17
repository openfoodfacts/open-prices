import csv
import datetime
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
    "quantity",  # extra
    "currency",
    "location",  # extra
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


def gdpr_source_field_cleanup_rules(gdpr_source, op_field, gdpr_field_value):
    """
    Rules to help build the price fields
    """
    if gdpr_source == "AUCHAN":
        if op_field == "price":
            gdpr_field_value = float(gdpr_field_value.replace(",", "."))
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
    elif gdpr_source == "INTERMARCHE":
        if op_field in ["price", "quantity"]:
            # divide price by quantity
            gdpr_field_value = float(gdpr_field_value.replace(",", "."))
        # input: 27/05/2021
        # output: 2021-05-27
        if op_field == "date":
            gdpr_field_value = datetime.datetime.strptime(
                gdpr_field_value, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")

    return gdpr_field_value


def gdpr_source_price_cleanup_rules(gdpr_source, gdpr_op_price):
    """
    Rules to cleanup the price object
    """
    if gdpr_source == "AUCHAN":
        pass
    elif gdpr_source == "CARREFOUR":
        pass
    elif gdpr_source == "INTERMARCHE":
        # price must be deviced by quantity
        gdpr_op_price["price"] = gdpr_op_price["price"] / gdpr_op_price["quantity"]

    return gdpr_op_price


def gdpr_source_filter_rules(op_price_list, gdpr_source=""):
    """
    Rules to skip some prices (on code, location...)
    """
    op_price_list_filtered = list()

    for op_price in op_price_list:
        passes_test = True
        if gdpr_source == "AUCHAN":
            if len(op_price["product_code"]) < 13:
                passes_test = False
            elif op_price["product_code"].endswith("000000"):
                passes_test = False
        elif gdpr_source == "CARREFOUR":
            pass
        elif gdpr_source == "INTERMARCHE":
            # filter location
            if op_price["location"] != "TO SET":
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
    requests.post(OPEN_PRICES_CREATE_PRICE_ENDPOINT, json=price, headers=headers)
    # if response.status_code == 201:
    #     print("Price created !")


if __name__ == "__main__":
    """
    How-to run:
    > FILEPATH= poetry run python data/gdpr/create_prices_from_gdpr_csv.py
    Required params: see REQUIRED_ENV_PARAMS
    """
    # Step 1: read input file
    filepath = os.environ.get("FILEPATH")
    print(f"===== Reading {filepath}")
    gdpr_price_list = read_gdpr_csv(filepath)
    print(len(gdpr_price_list))
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
    print(open_prices_price_list[0])

    # Step 4: filter prices depending on specific rules
    print("===== Applying filtering rules")
    open_prices_price_list_filtered = gdpr_source_filter_rules(
        open_prices_price_list, gdpr_source=source
    )
    print(len(open_prices_price_list_filtered))
    print(open_prices_price_list_filtered[0])

    # Step 5: send prices to backend via API
    if os.environ.get("DRY_RUN") == "False":
        print(f"===== Uploading data to {OPEN_PRICES_CREATE_PRICE_ENDPOINT}")
        progress = 0
        for index, price in enumerate(open_prices_price_list_filtered):
            create_price(price)
            # some pauses to be safe
            progress += 1
            if (progress % 10) == 0:
                time.sleep(1)
            if (progress % 50) == 0:
                print(f"{progress}/{len(open_prices_price_list_filtered)}...")
    else:
        sys.exit("No prices uploaded (DRY_RUN env missing or set to 'True')")
