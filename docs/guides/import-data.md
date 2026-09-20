# Import public exports into a local database

`import_public_data` loads the public locations, proofs and prices exports (JSONL
or gzip-compressed JSONL) into a local development database.

Use a PostgreSQL database with migrations applied, as described in
[Install](../community/INSTALL.md). The locations, proofs (including drafts) and
prices tables must be empty; existing products and local user accounts can remain.
Run the import before starting the application or its background workers.

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

Run the same command without `--dry-run` to import. Keep the input files unchanged
while the command runs.

- `--dry-run` validates values, IDs and references without writing to the database.
- For filtered exports, `--allow-missing-references` clears missing location, proof
  and duplicate-price links instead of rejecting the import.
- `--batch-size` sets the number of records inserted at once (default: 1000).
- The import preserves IDs and timestamps, rebuilds counters and resets ID
  sequences in one transaction.
- Products are matched by barcode or created as minimal records. Product details
  and proof images are not downloaded, and no background jobs are started.

See all command options and the [import script](https://github.com/openfoodfacts/open-prices/blob/main/open_prices/common/import_data.py)
for validation, transaction and performance details:

```sh
uv run --env-file .env python manage.py import_public_data --help
```
