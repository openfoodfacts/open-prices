# Uploading GDPR price data

## Context

One of our data sources is GDPR request to supermarkets (with fidelity cards).

See https://wiki.openfoodfacts.org/GDPR_request

## List of supermarkets

|Supermarket|Data              |Preprocessing|
|-----------|------------------|---|
|Auchan     |1 single file     ||
|Carrefour  |1 file with 2 tabs|- merge files<br/>- skip discounts|
|E.Leclerc  |2 files           |- merge files|
|Intermarché|1 single file     ||
|Picard     |1 file with multiple tables||

## Usage

### Step 1: get your API token from Open Prices

https://prices.openfoodfacts.org/api/docs#/auth/auth_create

### Step 2: upload a proof

Use the token returned in Step 1.

You can upload your proof via Postman (change the key to "File").

### Step 3: get your file ready

If the data comes in different files, use the `merge_two_csv_files.py` script (details below).

The file must be a `.csv`.

### Step 4: upload your file

#### For each location

Depending on the source, you'll need to provide the correct `LOCATION` key, and provide the corresponding `LOCATION_OSM_ID` & `LOCATION_OSM_TYPE`. You can use https://www.openstreetmap.org/ to pinpoint the corresponding places.

#### Upload command

Use the token returned in Step 1.

```
FILEPATH=../data/Carrefour/Carte_Carrefour_NAME_merged.csv SOURCE=CARREFOUR LOCATION="City Jaures Grenoble" LOCATION_OSM_ID=1697821864 LOCATION_OSM_TYPE=NODE PROOF_ID=1234 API_ENDPOINT=https://prices.openfoodfacts.net/api/v1 API_TOKEN=username_token-hash poetry run python scripts/gdpr/create_prices_from_gdpr_csv.py
```

Last changes when you're ready:
- replace the API_ENDPOINT with `https://prices.openfoodfacts.org/api/v1`
-  `DRY_RUN=False` to actually upload your data

## Other tools

### Merge two csv files

Script name: `merge_two_csv_files.csv`

Goal: merge and enrich data from the second csv file into the first csv file.

E.Leclerc returns 2 different files, one containing a list of receipts (with dates & locations), and the other a list of products with their receipt id. So we need to first merge the 2 files into 1.
```
(TODO)
```

For Carrefour, the file contains 2 tabs, 1 called "Tickets" and the other called "Remise".
```
FILEPATH_1=Carte_Carrefour_NAME_liste_tickets_Tickets.csv FILEPATH_2=Carte_Carrefour_NAME_liste_tickets_Remises.csv PIVOT_FIELD_NAME_LIST="Numéro du ticket de caisse magasin,Code Barre du produit,Description du produit" poetry run python scripts/gdpr/merge_two_csv_files.py
```
