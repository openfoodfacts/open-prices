# Uploading shop price data

## Context

One of our data sources is shop imports (supermarkets uploading data directly).

For instance, some members are active volunteers in food co-ops, and get authorization to extract and upload price data from their shops.

## Usage

### Step 0: prerequisites

* have a .csv file of the prices
* upload these prices to a dedicated shop account please! See other shops for examples: `elefan-grenoble`, `400coop-paris11`

### Step 1: create a JSON mapping file

Similar to existing mapping files, create your own!
* with the list of fields
* and optional filter rules

### Step 2: get your API token from Open Prices

https://prices.openfoodfacts.org/api/docs#/auth/auth_create

### Step 3: upload a proof

Use the token returned in Step 1.

You can upload your proof via Postman (change the key to "File").

### Step 4: get your file ready

The file must be a `.csv`.

### Step 5: upload your file

Use the token returned in Step 1.

```
FILEPATH=../data/Elefan/20241208_articles_actif.csv MAPPING_FILEPATH=scripts/shop_import/mappings/elefan_grenoble.json DATE=2024-12-08 PROOF_ID=1234 API_ENDPOINT=https://prices.openfoodfacts.net/api/v1 API_TOKEN=<username__token-hash> DRY_RUN=True poetry run python scripts/shop_import/create_prices_from_csv.py
```

Last changes when you're ready:
- replace the `API_ENDPOINT` with `https://prices.openfoodfacts.org/api/v1`
- set `DRY_RUN` to `False` to actually upload your data
