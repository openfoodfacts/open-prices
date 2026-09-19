# Import public exports into a local database

`import_public_data` loads the public locations, proofs and prices exports into a
development database. It accepts both JSONL and gzip-compressed JSONL. These are
API exports, rather than Django fixtures for `loaddata`.

Use a PostgreSQL database with migrations applied, as described in
[Install](../community/INSTALL.md). Other database engines are explicitly rejected.
The locations, proofs (including drafts) and prices tables must be empty. Existing
product metadata and local user accounts can be retained. The command refuses to
merge or overwrite an existing price dataset. It does not create a database or
delete any existing records.

## Download

The public files are listed in the [data guide](data.md). Download all three:

```sh
mkdir -p /tmp/open-prices-exports
for name in locations proofs prices; do
  curl --fail --location "https://prices.openfoodfacts.org/data/${name}.jsonl.gz" \
    --output "/tmp/open-prices-exports/${name}.jsonl.gz" || exit 1
done
```

## Validate and import

From the repository root, with `.env` pointing to your development database:

```sh
uv run --env-file .env python manage.py import_public_data \
  --locations /tmp/open-prices-exports/locations.jsonl.gz \
  --proofs /tmp/open-prices-exports/proofs.jsonl.gz \
  --prices /tmp/open-prices-exports/prices.jsonl.gz \
  --dry-run
```

`--dry-run` parses the files and checks field values, duplicate IDs and references
without inserting records or advancing database sequences. Errors identify the
file and line. By default, all referenced locations, proofs and duplicate prices
must be present in the supplied files.

For filtered exports, add `--allow-missing-references` to replace missing
location, proof and duplicate-price links with `NULL`. Valid links are preserved,
including duplicate prices appearing later in the file. The command reports how
many references were cleared; with `--dry-run`, it reports how many would be
cleared without writing. Invalid values, duplicate IDs and self-referencing
duplicate prices still fail validation. Counters reflect the remaining links.
Products always resolve by `product_code`; without a code, their link is `NULL`,
regardless of the source `product_id`.

Run the same command without `--dry-run` to import. `--batch-size` controls the
number of records inserted at once (default: 1000). Files are read twice, for
validation and insertion; memory holds IDs, a product-code-to-ID cache, any missing
references and a batch of records, rather than the complete decompressed dataset.
Keep the input files unchanged while running.

The import:

- Loads locations, proofs and prices in one transaction. An error rolls back the
  imported rows and counter changes.
- Preserves their IDs, timestamps, decimal values and duplicate-price links,
  including references to later prices in the file.
- Resolves products by `product_code`, reusing local products or creating minimal
  product rows. Source `product_id` values are not local database identifiers.
- Recomputes location, proof and product counters, existing local user counters,
  and the application's total statistics. Prediction counts are zero because
  predictions are not part of these exports.
- Resets the imported tables' ID sequences so subsequent inserts remain valid.
- Bypasses model save hooks: it does not create historical changes, run OCR/ML,
  enqueue background jobs, or call Open Food Facts/OpenStreetMap.

The command locks the affected tables against concurrent writes during import;
run it before using the development app or starting its background workers.

## Performance

Product IDs are cached between batches. Existing products are looked up once per
code, and new products use the IDs returned by PostgreSQL's bulk insert. Location
counters are rebuilt in a single table update.

Preserving source `updated` timestamps requires a bulk update after each bulk
insert, because Django's `auto_now` replaces them during insertion. This adds an
update for each imported row with that timestamp (about 314,000 price rows in a
September 2026 export, plus locations and proofs). These updates run in batches,
but still add substantial write volume.

Existing local user counters reuse `User.update_task()`, which performs several
queries and five `save()` calls per user. This is suitable for a development
database with few local accounts; a large existing user table will take longer.

## Product details and proof images

The exports contain product codes, but no complete product catalog. Prices without
a barcode already include `category_tag` and need no product enrichment.

For barcode products, names, brands and product images can be fetched separately
using the existing Open Food Facts helper. This optional step performs network
requests and may take time for a large dataset:

```sh
uv run --env-file .env python manage.py shell <<'PY'
from open_prices.products.models import Product
from open_prices.products.tasks import fetch_and_save_data_from_openfoodfacts
from open_prices.stats.models import TotalStats

for product in Product.objects.filter(price_count__gt=0, source__isnull=True).iterator():
    fetch_and_save_data_from_openfoodfacts(product)
TotalStats.get_solo().update_product_stats()
PY
```

Products not found in Open Food Facts remain minimal product rows. For bulk
catalog synchronization, see [Open Food Facts product data](../topics/open-food-facts-product-data.md).

Proof records contain image paths, not image files. The importer preserves these
paths but does not download images; local proof previews require the corresponding
files under the configured images directory. Accounts, predictions, price tags,
history, challenges and moderation data are not included in the three exports.
