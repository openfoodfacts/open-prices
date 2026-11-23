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

- Live, with Redis: Open Prices listens to the Product Opener `product_updates` stream (all 4 flavors). On each `created` / `updated` event, the product is re-fetched from the API of its flavor (`deleted` removes it). See `open_prices/products/management/commands/run_update_listener.py`
- On product creation in Open Prices (e.g. a price for an unknown barcode), the product data is fetched from the Open Food Facts API
- The daily batch imports of the OxF dumps (`import_product_db`) are disabled in production, but can be re-enabled with the `ENABLE_IMPORT_*_DB_TASK` env variables (e.g. for a full resync)
