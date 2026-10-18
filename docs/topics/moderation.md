# Moderation

Open Prices relies on moderation to improve data quality over time.

## Flags 🚩

Any logged-in contributor can flag a `Price` or a `Proof`.

A flag has:

- a `reason`: `WRONG_TYPE`, `WRONG_PRICE_VALUE`, `WRONG_CURRENCY`, `WRONG_PRODUCT`, `WRONG_LOCATION`, `WRONG_DATE` or `OTHER`
- an optional `comment`
- a `status`: `OPEN` (default) or `CLOSED`
- an `owner` (the user who flagged)
- a `source` (the app used)

API endpoints:

- `POST /api/v1/prices/{id}/flag` & `POST /api/v1/proofs/{id}/flag`: create a flag (logged-in users)
- `GET /api/v1/flags`: list flags, filterable by `content_type`, `object_id`, `reason` & `status` (moderators only)
- `PATCH /api/v1/flags/{id}`: update a flag's `status` (moderators only)

see the "moderation" section of the [API docs](https://prices.openfoodfacts.org/api/docs)

## Moderators 🛡️

A few contributors have moderation rights (`is_moderator` on the `User`, set via the Django admin). Moderators can:

- review flags in the [moderation dashboard](https://prices.openfoodfacts.org/moderation)
- edit or delete any `Price` or `Proof` (other contributors can only edit or delete their own)
- close flags once handled

Before editing or deleting an object, moderators can check its [History](history.md).

## Automated rules 🤖

Some moderation runs automatically, as scheduled tasks (see `open_prices/common/tasks.py`):

- **price outliers** (daily): prices that are much higher or lower than the product's median get a `WRONG_PRICE_VALUE` flag, with `source="outlier-detection"`. See [Price outlier detection](outlier-detection.md)
- **barcode cleanup** (daily): for products with a long (> 13 digits) or invalid barcode, unknown to Open Food Facts, prices created through the price tag validation workflows are deleted. The product is then deleted if it has no prices left
