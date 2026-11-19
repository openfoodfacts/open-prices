# API

## Documentation

### Links

- pre-prod: [https://prices.openfoodfacts.net/api/docs](https://prices.openfoodfacts.net/api/docs)
- production: [https://prices.openfoodfacts.org/api/docs](https://prices.openfoodfacts.org/api/docs)

### Environments

We have two environments:

- pre-production: for testing and staging
- production: for the live data. ⚠️ Please test your scripts on pre-production before running them on production.

### Authentication

- Some endpoints require authentication
- You will need to create an account on [Open Food Facts](https://world.openfoodfacts.org). Then generate a `token` through the dedicated Open Prices endpoint.
  - when switching from pre-production to production, the account stays the same, but you will need to generate a new token
- Authentication method: Bearer token in the `Authorization` header

## Add prices through the API

Use a dedicated Open Food Facts account for your application so its contributions can be attributed to it. Start with a real price you have checked against its source photo. Test the integration in pre-production before sending any writes to production.

The examples use Bash, `curl`, and `jq`. Replace the file, date, currency, shop, barcode, and price with values from the same observation.

### 1. Get an Open Prices token

Use your Open Food Facts **user ID** (not your email address) and password. `POST /api/v1/auth` accepts form data and returns an `access_token`. Keep the password and token out of source files and logs.

```bash
base_url=https://prices.openfoodfacts.net/api/v1
read -r -p 'Open Food Facts user ID: ' off_user
read -rs -p 'Open Food Facts password: ' off_password
printf '
'
token=$(
    printf '%s' "$off_password" |
        curl --fail-with-body --silent --show-error \
            --data-urlencode "username=$off_user" \
            --data-urlencode 'password@-' \
            "$base_url/auth" |
        jq -er '.access_token'
)
unset off_password
```

Check that authentication succeeded before moving on. For an integration already using Open Food Facts single sign-on, the same endpoint accepts its Keycloak access token as the form field `access_token` instead of a user ID and password. Use the **returned Open Prices token** in the `Authorization: Bearer …` header. Get a separate token when switching environments.

### 2. Upload the photo as a proof

A proof is the source photo for one or more price records. For a receipt, use `RECEIPT`; for a shelf-label image, use `PRICE_TAG`. The multipart endpoint requires `file` and `type`. Include the date, currency, and shop to make the proof usable for verification. Remove personal information such as loyalty or payment details from receipts before uploading.

For a physical shop, supply its OpenStreetMap element ID and type (`NODE`, `WAY`, or `RELATION`). You can upload directly without calling the Locations API first. Open Prices resolves the OSM pair and creates the location if needed. For an existing online shop, use its Open Prices `location_id` instead and leave both OSM fields out. See [OpenStreetMap location data](../topics/openstreetmap-location-data.md).

```bash
observation_date=2026-01-15
currency=EUR
osm_type=NODE
osm_id=652825274

proof_id=$(
    curl --fail-with-body --silent --show-error \
        --header "Authorization: Bearer $token" \
        --form 'file=@shelf-label.jpg' \
        --form 'type=PRICE_TAG' \
        --form "date=$observation_date" \
        --form "currency=$currency" \
        --form "location_osm_type=$osm_type" \
        --form "location_osm_id=$osm_id" \
        "$base_url/proofs/upload" |
        jq -er --arg currency "$currency" --arg osm_type "$osm_type" \
            --argjson osm_id "$osm_id" '
            if .currency == $currency and .location_osm_type == $osm_type
                and .location_osm_id == $osm_id
            then .id
            else error("Uploaded proof has a different currency or shop")
            end'
)
```

Continue only once you have a verified proof ID. Uploading an identical photo with the same owner, proof type, date, and OSM fields can return an existing proof. The duplicate check ignores currency and the internal `location_id`. For an online shop, compare the returned currency and `location_id` with your observation before using its ID. If they differ, check the existing proof against the photo before correcting it or selecting another proof.

Enabled server jobs can extract text or detect price tags asynchronously. To make a shelf photo available in the price-tag validation workflow, send `ready_for_price_tag_validation=true` as an additional form field on a `PRICE_TAG` proof. The flag defaults to false and does not turn predictions into verified prices. A duplicate upload returns the existing flag. If you own that proof and want to enable validation, check the returned flag and update the proof directly with `PATCH /api/v1/proofs/{id}` when needed. See the [proof prediction flow](../topics/ai/proof-prediction-flow.md) for which jobs may run.

### 3. Add a price linked to that proof

Send the returned proof ID as `proof_id` and include `price` and a product identifier. For a packaged product, send its barcode **as a string** in `product_code`. For a bulk product without a barcode, send `type: "CATEGORY"`, a language-prefixed `category_tag` such as `en:apples`, and a `price_per` of `UNIT`, `KILOGRAM`, or `LITER` in place of the barcode.

Repeat the proof's date, currency, and location information. When you create a price, the API checks its date, currency, and OSM fields against the corresponding values on a shelf-tag or receipt proof when those values are set. It does not copy these fields from the proof. For an online shop, send the proof's `location_id` instead of the OSM pair and check that the IDs match yourself. The API's proof-to-price check does not compare that field.

```bash
jq -n \
    --argjson proof_id "$proof_id" \
    --arg product_code '8001505005707' \
    --argjson price 2.49 \
    --arg date "$observation_date" \
    --arg currency "$currency" \
    --argjson location_osm_id "$osm_id" \
    --arg location_osm_type "$osm_type" \
    '$ARGS.named' |
    curl --fail-with-body --silent --show-error \
        --header "Authorization: Bearer $token" \
        --header 'Content-Type: application/json' \
        --data-binary @- \
        "$base_url/prices"
```

Check that the response identifies the new price. Repeat the last step for each verified price in the photo, reusing the same `proof_id`. Submit only prices checked by a person against the photo. Unverified automated prices may be removed by moderators. See the [data quality rules](../topics/data-quality.md) for validation, discounts, and duplicate handling.

## License

Make sure you comply with the OdBL licence, mentioning the source of your data, and ensuring to avoid combining non free data you can't release legally as open data. Another requirement is contributing back any product you add using this SDK.

## Reuse

see [Reuses](../community/reuses.md)
