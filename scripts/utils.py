import csv
import json
from datetime import datetime

import requests


def read_csv(filepath, delimiter=","):
    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        return list(reader)


def read_json(filepath):
    with open(filepath) as jsonfile:
        return json.load(jsonfile)


def is_valid_date(date_str):
    """
    - check if string
    - check if it has the format YYYY-MM-DD
    - check if valid ISO 8601 format
    """
    if not isinstance(date_str, str):
        return False
    if len(date_str) != 10:
        return False
    if date_str[4] != "-" or date_str[7] != "-":
        return False
    try:
        datetime.fromisoformat(date_str)
    except ValueError:
        return False
    return True


def create_price(price, API_ENDPOINT, API_TOKEN):
    OPEN_PRICES_CREATE_PRICE_ENDPOINT = f"{API_ENDPOINT}/prices"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(
        OPEN_PRICES_CREATE_PRICE_ENDPOINT, json=price, headers=headers
    )
    if not response.status_code == 201:
        print(response.json())
        print(price)
