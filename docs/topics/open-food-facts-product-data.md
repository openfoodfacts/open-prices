# Open Food Facts (Product data)

Open Prices relies on Open Food Facts product data.

## Why

Having product data directly in Open Prices allows for a better contributor experience and easy filtering/aggregation/stats.

## What is used

### Backend

- Product table
    - all 4 product flavors (food, beauty, pet food, products, as well as obsolete food products) are stored
    - we keep only a subset of fields (code, name, brands, categories...)
- Taxonomies
    - we manipulate taxonomies for specific use cases (e.g. challenges)
- Contributing back
    - we allow creating products back to OFF (with the `open-prices` username)
- all thanks to [openfoodfacts-python](https://github.com/openfoodfacts/openfoodfacts-python)

see `open_prices/common/openfoodfacts.py`

### Frontend

- Taxonomies (categories, labels, origins, languages) are used in some forms
    - thanks to [openfoodfacts-python](https://github.com/openfoodfacts/openfoodfacts-python)
    - see [https://github.com/openfoodfacts/open-prices-frontend/tree/main/data](https://github.com/openfoodfacts/open-prices-frontend/tree/main/data)
- Barcode scanner
    - thanks to [openfoodfacts-webcomponents](https://github.com/openfoodfacts/openfoodfacts-webcomponents)

## Data sync

With Redis, Open Prices gets instant product changes.

There is also a daily batch sync to be sure we don't miss anything.
