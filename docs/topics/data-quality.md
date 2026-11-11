# Data quality

Open Prices relies on several mechanisms to keep its data reliable: some run on every save, some run daily, and some rely on the community.

| Mechanism | When | See |
|---|---|---|
| Validation & normalization | on each save | [below](#validation-normalization) |
| Duplicate prices | on each save (+ manual scripts) | [below](#duplicate-prices) |
| Duplicate proofs | on upload (+ manual scripts) | [below](#duplicate-proofs) |
| Price outliers | daily | [Price outlier detection](outlier-detection.md) |
| Barcode cleanup | daily | [Moderation](moderation.md#automated-rules) |
| Flags & moderators | anytime | [Moderation](moderation.md) |
| History | on each save | [History](history.md) |

## Validation & normalization ✅

Every `Price` (and `Proof`) is validated before being saved. Invalid data is rejected with a `400` by the API.

For prices, the main rules are:

- **product or category**: a `PRODUCT` price needs a `product_code` (letters & numbers only), a `CATEGORY` price needs a `category_tag` and a `price_per`
- **price**: must be set. If `price_without_discount` is set, it must be greater than `price`, and `price_is_discounted` must be `True`
- **date**: must not be in the future
- **location & proof**: must exist. On creation, the price location must match the location's (or proof's) OSM id & type, and for single-shop proofs (price tag, receipt, shop import) the price date & currency must match the proof's
- **proof owner**: a user can only add prices to their own proofs (except price tag proofs, open to any user)

Some fields are also normalized: barcodes are padded to 8 or 13 digits, and taxonomy tags (`category_tag`, `labels_tags`, `origins_tags`) are converted to their canonical form.

See `open_prices/prices/validators.py` & `open_prices/proofs/validators.py` for the full list.

## Duplicate prices 👯

### Detection (automatic)

On each save, a price is marked as a duplicate (`duplicate_of` field) of an older price if they share the same type, location, date, currency, price fields (`price`, `price_per`, discount fields), product (`product_code` or `category_tag`), `labels_tags` and `origins_tags`. Prices without a location or a date are never considered duplicates.

Duplicates are kept in the database. API consumers can hide them with the `duplicate_of__isnull=true` filter.

If a duplicate price is edited and no longer matches, the `duplicate_of` field is reset. When the original price is deleted, its duplicates are re-evaluated.

### Cleanup (manual)

Two management commands are available (not scheduled, run with `make cli args='<command>'`):

- `update_duplicate_of_field`: (re)compute `duplicate_of` on existing prices
- `remove_duplicate_prices`: delete duplicate prices coming from the same `PRICE_TAG` proof (same `product_code` & `price`), keeping the one with the lowest ID. Dry run by default, use `--apply` to delete

## Duplicate proofs 🖼️

### Detection (on upload)

The MD5 hash of each uploaded image is stored (`image_md5_hash` field).

When a user uploads a proof with the same image hash, type, location and date as one of their existing proofs, the new file is discarded and the existing proof is returned (with `"detail": "duplicate"`).

Only exact copies are detected: the same image uploaded by another user, or a new photo of the same receipt, is not considered a duplicate.

### Cleanup (manual)

Two management commands are available (not scheduled, run with `make cli args='<command>'`):

- `compute_missing_image_hash`: compute the image hash of older proofs that don't have it yet
- `remove_duplicate_proofs`: for proofs with the same owner, date, type, location and image hash, keep the one with the lowest ID, move the prices of the other proofs to it, and delete them. Dry run by default, use `--apply` to delete
