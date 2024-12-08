# Uploading shop price data

## Context

One of our data sources is shop imports (supermarkets uploading data directly).

Currently, some members are active volunteers in food co-ops, and get authorization to extract and upload data from their shops.

## Usage

### Step 0: prerequisites

* have a .csv file of the prices
* upload these prices to a dedicated shop account please! See other shops for examples: `elefan-grenoble`, `400coop-paris11`

### Step 1: get your API token from Open Prices

https://prices.openfoodfacts.org/api/docs#/auth/auth_create

### Step 2: upload a proof

Use the token returned in Step 1.

You can upload your proof via Postman (change the key to "File").

### Step 3: get your file ready

The file must be a `.csv`.

### Step 4: upload your file

#### Upload command

Use the token returned in Step 1.

```
FILEPATH=../data/Elefan/20241208_articles_actif.csv PRODUCT_CODE_FIELD=Code PRODUCT_NAME_FIELD=Designation PRICE_FIELD="Prix Vente (€)" CURRENCY=EUR LOCATION_OSM_ID=1392117416 LOCATION_OSM_TYPE=NODE DATE=2024-12-08 PROOF_ID=1234 API_ENDPOINT=https://prices.openfoodfacts.net/api/v1 API_TOKEN=username_token-hash poetry run python scripts/shop_import/create_prices_from_csv.py
```

Last changes when you're ready:
- replace the API_ENDPOINT with `https://prices.openfoodfacts.org/api/v1`
-  `DRY_RUN=False` to actually upload your data
