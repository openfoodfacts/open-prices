import csv

import requests


def read_csv(filepath, delimiter=","):
    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        return list(reader)


def create_price(price, API_ENDPOINT, API_TOKEN):
    OPEN_PRICES_CREATE_PRICE_ENDPOINT = f"{API_ENDPOINT}/prices"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(
        OPEN_PRICES_CREATE_PRICE_ENDPOINT, json=price, headers=headers
    )
    if not response.status_code == 201:
        print(response.json())
        print(price)
