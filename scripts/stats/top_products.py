import time

import requests

OPEN_PRICES_PRODUCT_ENDPOINT = "https://prices.openfoodfacts.org/api/v1/products"  # page=1&size=10&order_by=-unique_scans_n&source=off


def get_product_list(count=100, source="off"):
    """
    Get the list of products from Open Prices
    """
    product_list = list()

    # loop the API
    page = 1
    size = 100
    while len(product_list) < count:
        url = f"{OPEN_PRICES_PRODUCT_ENDPOINT}?page={page}&size={size}&order_by=-unique_scans_n&source={source}"
        print(url, len(product_list))
        response = requests.get(url)
        if response.status_code == 200:
            product_list += response.json()["items"]
            page += 1
            time.sleep(1)
        else:
            break

    return product_list


def aggregate_product_list(product_list, field="price_count"):
    result = {"True": 0, "False": 0}

    for product in product_list:
        if product[field]:
            result["True"] += 1
        else:
            result["False"] += 1

    return result


if __name__ == "__main__":
    """
    How-to run:
    > poetry run python scripts/stats/top_products.py
    """
    # Step 1: get the list of products from OP
    product_list = get_product_list(count=1000)
    print(len(product_list))

    # Step 2: counts
    result = aggregate_product_list(product_list, field="price_count")
    print(result)
