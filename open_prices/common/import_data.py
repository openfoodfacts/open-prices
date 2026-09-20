"""Load public API exports with the ``import_public_data`` management command.

Inputs and destination
----------------------
The locations, proofs and prices inputs are JSONL or gzip-compressed JSONL API
exports, not Django fixtures for ``loaddata``. Use PostgreSQL with migrations
applied and empty locations, proofs (including drafts) and prices tables. Existing
product metadata and local accounts are retained; this command neither creates
the database nor deletes or merges an existing price dataset. Run it before
starting the development app or its workers: the import locks location, proof,
price and product tables against concurrent writes.

Validation and import
---------------------
``--dry-run`` checks field values, duplicate IDs and references without inserting
records or advancing sequences. Errors identify the input file and line. By
default, all referenced locations, proofs and duplicate prices must be included.
``--allow-missing-references`` clears missing links to NULL for filtered exports
and reports their count, including during a dry run. Invalid values, duplicate
IDs and self-referencing duplicate prices still fail. Valid links are preserved,
including duplicates pointing to prices later in the file.

The import runs in one transaction; errors roll back rows and counter changes.
It preserves source IDs, timestamps and decimal values, rebuilds location, proof,
product, existing local user and total counters, then resets imported ID
sequences. Products resolve by ``product_code``, reusing local rows or creating
minimal ones. Source ``product_id`` values are ignored; without a code, the local
product link is NULL. Counters reflect only the remaining links, and prediction
counts are zero because predictions are not imported.

Files are read twice, so keep them unchanged during the command. Memory holds
IDs, product codes and their local ID cache, missing references and one batch of
records. ``--batch-size`` controls batch writes (default: 1000; must be positive).
Existing products are looked up once per code; bulk inserts return new product
IDs. Location counters use one table update. Restoring ``updated`` timestamps
after Django's ``auto_now`` requires an additional bulk update per batch. Local
user counters use ``User.update_task()``, with several queries and five saves per
user, so a large existing user table makes the import slower.

Data outside the exports
------------------------
Bulk writes bypass model save hooks: no history, OCR, prediction jobs or external
requests are triggered. Accounts, predictions, price tags, history, challenges
and moderation data are not imported. Proof image paths are preserved, but the
image files must be supplied separately under the configured images directory.
Category prices already contain ``category_tag`` and need no product enrichment.

To optionally fetch barcode product names, brands and images, run the following
in ``manage.py shell`` after importing. This makes network requests and may take
time; products absent from Open Food Facts remain minimal rows. For bulk catalog
synchronization, see ``docs/topics/open-food-facts-product-data.md``.

    from open_prices.products.models import Product
    from open_prices.products.tasks import fetch_and_save_data_from_openfoodfacts
    from open_prices.stats.models import TotalStats

    for product in Product.objects.filter(price_count__gt=0, source__isnull=True).iterator():
        fetch_and_save_data_from_openfoodfacts(product)
    TotalStats.get_solo().update_product_stats()
"""

import gzip
import json
import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.db import DatabaseError, connection, models, transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.products.models import Product
from open_prices.proofs.models import Proof
from open_prices.stats.models import TotalStats
from open_prices.users.models import User

# This mapping follows the public Location/Proof/PriceSerializer exports. Ignore
# Location's computed logo URL and Price's source-database product IDs (both
# aliases); products are resolved locally by product_code. COUNT_FIELDS are also
# ignored and rebuilt. All other concrete fields are copied by name, preferring
# the *_id alias for relations. Review this contract when serializers add aliases
# or computed fields whose names overlap model columns.
IGNORED_EXPORT_FIELDS = {
    Location: {"osm_brand_logo_url"},
    Proof: set(),
    Price: {"product", "product_id"},
}


@dataclass
class ImportPlan:
    counts: dict[str, int]
    product_codes: set[str]
    duplicates: list[tuple[int, int, int]]
    missing_references: dict[str, dict[int, set[str]]]

    @property
    def missing_reference_count(self) -> int:
        return sum(
            len(fields)
            for rows in self.missing_references.values()
            for fields in rows.values()
        )


def positive_id(value: Any) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("IDs must be positive integers")
    return value


def read_objects(path: Path, model: type[models.Model]) -> Iterator[tuple[int, Any]]:
    """Convert concrete fields only; API properties are not database columns."""
    line_number = 0
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                row = json.loads(line, parse_float=Decimal)
                if not isinstance(row, dict):
                    raise ValueError("expected a JSON object")
                values = {"id": positive_id(row.get("id"))}
                for field in model._meta.concrete_fields:
                    if field.primary_key or field.name in IGNORED_EXPORT_FIELDS[model]:
                        continue
                    if field.name in getattr(model, "COUNT_FIELDS", ()):
                        values[field.attname] = 0
                        continue
                    key = field.attname if field.attname in row else field.name
                    if key not in row:
                        if not (
                            field.has_default()
                            or field.null
                            or getattr(field, "auto_now", False)
                        ):
                            raise ValueError(f"missing field {field.name!r}")
                        continue
                    value = row[key]
                    if field.is_relation:
                        value = positive_id(value) if value is not None else None
                    elif value is not None or not field.null:
                        value = field.clean(value, None)
                    values[field.attname] = value
                yield line_number, model(**values)
    except (
        OSError,
        EOFError,
        UnicodeError,
        ValueError,
        TypeError,
        ValidationError,
        zlib.error,
    ) as exc:
        raise CommandError(f"{path}:{line_number}: {exc}") from exc


def validate_exports(
    paths: dict[str, Path], *, allow_missing_references: bool = False
) -> ImportPlan:
    """Read without writing, keeping IDs rather than complete records in memory."""
    identifiers: dict[str, set[int]] = {}
    codes: set[str] = set()
    duplicates: list[tuple[int, int, int]] = []
    missing_references: dict[str, dict[int, set[str]]] = {}
    location_keys: set[tuple[Any, ...]] = set()
    for name, model in (("locations", Location), ("proofs", Proof), ("prices", Price)):
        seen: set[int] = set()
        for line, obj in read_objects(paths[name], model):
            prefix = f"{paths[name]}:{line}"
            if obj.pk in seen:
                raise CommandError(f"{prefix}: duplicate ID {obj.pk}")
            seen.add(obj.pk)
            if model is Location:
                key: tuple[Any, ...] | None = None
                if (
                    obj.type == location_constants.TYPE_OSM
                    and obj.osm_id is not None
                    and obj.osm_type is not None
                ):
                    key = (obj.type, obj.osm_id, obj.osm_type)
                elif (
                    obj.type == location_constants.TYPE_ONLINE
                    and obj.website_url is not None
                ):
                    key = (obj.type, obj.website_url)
                if key is not None:
                    if key in location_keys:
                        raise CommandError(f"{prefix}: duplicate location {key}")
                    location_keys.add(key)
            else:
                for field, target in (
                    ("location_id", "locations"),
                    ("proof_id", "proofs"),
                ):
                    reference = getattr(obj, field, None)
                    if reference is not None and reference not in identifiers[target]:
                        if not allow_missing_references:
                            raise CommandError(f"{prefix}: unknown {field} {reference}")
                        missing_references.setdefault(name, {}).setdefault(
                            obj.pk, set()
                        ).add(field)
            if model is Price:
                if obj.product_code:
                    codes.add(obj.product_code)
                if obj.duplicate_of_id is not None:
                    duplicates.append((obj.pk, obj.duplicate_of_id, line))
        identifiers[name] = seen
    valid_duplicates = []
    for pk, reference, line in duplicates:
        if reference == pk or reference not in identifiers["prices"]:
            if reference == pk or not allow_missing_references:
                raise CommandError(
                    f"{paths['prices']}:{line}: invalid duplicate_of {reference}"
                )
            missing_references.setdefault("prices", {}).setdefault(pk, set()).add(
                "duplicate_of_id"
            )
        else:
            valid_duplicates.append((pk, reference, line))
    return ImportPlan(
        {name: len(ids) for name, ids in identifiers.items()},
        codes,
        valid_duplicates,
        missing_references,
    )


def require_empty_destination() -> None:
    for model in (Location, Proof, Price):
        if model._base_manager.exists():
            raise CommandError(
                f"{model._meta.db_table} is not empty. Use a fresh database; "
                "this command never merges or overwrites existing data."
            )


def insert_batch(
    model: type[models.Model],
    objects: list[Any],
    batch_size: int,
    product_ids: dict[str, int],
) -> None:
    if model is Price:
        codes = {
            obj.product_code
            for obj in objects
            if obj.product_code and obj.product_code not in product_ids
        }
        if codes:
            products = Product.objects.in_bulk(codes, field_name="code")
            created = Product.objects.bulk_create(
                [Product(code=code) for code in codes if code not in products],
                batch_size=batch_size,
            )
            product_ids.update({code: product.pk for code, product in products.items()})
            # PostgreSQL returns the generated primary keys from bulk_create.
            product_ids.update({product.code: product.pk for product in created})
        for obj in objects:
            obj.product_id = product_ids[obj.product_code] if obj.product_code else None
            # A duplicate can point to a price appearing in a later batch.
            obj.duplicate_of_id = None
    timestamps = [obj.updated for obj in objects]
    model._base_manager.bulk_create(objects, batch_size=batch_size)
    # bulk_create runs DateTimeField.pre_save(), including auto_now fields.
    preserved = []
    for obj, updated in zip(objects, timestamps, strict=True):
        if updated is not None:
            obj.updated = updated
            preserved.append(obj)
    model._base_manager.bulk_update(preserved, ["updated"], batch_size=batch_size)


def count_updates(
    source: Any, foreign_key: str, counts: dict[str, Any]
) -> dict[str, Any]:
    related = (
        source.filter(**{foreign_key: OuterRef("pk")}).order_by().values(foreign_key)
    )
    return {
        name: Coalesce(Subquery(related.annotate(value=expression).values("value")), 0)
        for name, expression in counts.items()
    }


def rebuild_counts() -> None:
    Proof.all_objects.update(
        **count_updates(Price.objects.all(), "proof_id", {"price_count": Count("id")})
    )
    Location.objects.update(
        **count_updates(
            Price.objects.all(),
            "location_id",
            {
                "price_count": Count("id"),
                "product_count": Count("product_id", distinct=True),
            },
        ),
        **count_updates(
            Proof.objects.all(),
            "location_id",
            {
                "proof_count": Count("id"),
                "user_count": Count("owner", distinct=True),
            },
        ),
    )
    zero_counts = dict.fromkeys(Product.COUNT_FIELDS, 0)
    Product.objects.exclude(**zero_counts).update(**zero_counts)
    products = Product.objects.filter(
        pk__in=Price.objects.exclude(product_id=None).values("product_id")
    )
    products.update(
        **count_updates(
            Price.objects.all(),
            "product_id",
            {
                "price_count": Count("id"),
                "price_currency_count": Count("currency", distinct=True),
                "location_count": Count("location_id", distinct=True),
                "location_type_osm_country_count": Count(
                    "location__osm_address_country",
                    distinct=True,
                    filter=Q(location__type=location_constants.TYPE_OSM),
                ),
                "user_count": Count("owner", distinct=True),
                "proof_count": Count("proof_id", distinct=True),
            },
        ),
    )
    # Public exports contain owner names, not user accounts. Only update accounts
    # that already exist locally, using the application's existing calculations.
    User.update_task()
    TotalStats.update_task()
    # The public product manager can return an old PostgreSQL row estimate for
    # an unfiltered count when importing into an existing product catalog.
    TotalStats.objects.update(product_count=Product._base_manager.count())


def import_exports(
    paths: dict[str, Path],
    *,
    batch_size: int = 1000,
    dry_run: bool = False,
    allow_missing_references: bool = False,
) -> ImportPlan:
    if connection.vendor != "postgresql":
        raise CommandError("import_public_data requires PostgreSQL.")
    if batch_size < 1:
        raise CommandError("batch_size must be positive")
    require_empty_destination()
    plan = validate_exports(paths, allow_missing_references=allow_missing_references)
    if dry_run:
        return plan
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                tables = ", ".join(
                    connection.ops.quote_name(model._meta.db_table)
                    for model in (Location, Proof, Price, Product)
                )
                cursor.execute(f"LOCK TABLE {tables} IN SHARE ROW EXCLUSIVE MODE")
            require_empty_destination()
            product_ids: dict[str, int] = {}
            for name, model in (
                ("locations", Location),
                ("proofs", Proof),
                ("prices", Price),
            ):
                batch = []
                for _line, obj in read_objects(paths[name], model):
                    for field in plan.missing_references.get(name, {}).get(obj.pk, ()):
                        setattr(obj, field, None)
                    batch.append(obj)
                    if len(batch) == batch_size:
                        insert_batch(model, batch, batch_size, product_ids)
                        batch = []
                if batch:
                    insert_batch(model, batch, batch_size, product_ids)
            for start in range(0, len(plan.duplicates), batch_size):
                Price.objects.bulk_update(
                    [
                        Price(id=pk, duplicate_of_id=reference)
                        for pk, reference, _ in plan.duplicates[
                            start : start + batch_size
                        ]
                    ],
                    ["duplicate_of"],
                    batch_size=batch_size,
                )
            rebuild_counts()
            connection.check_constraints()
            with connection.cursor() as cursor:
                for sql in connection.ops.sequence_reset_sql(
                    no_style(), [Location, Proof, Price]
                ):
                    cursor.execute(sql)
    except DatabaseError as exc:
        raise CommandError(f"Import rolled back: {exc}") from exc
    return plan
