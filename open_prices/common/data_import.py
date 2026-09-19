"""Load the public API JSONL exports into an empty development database."""

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


@dataclass
class ImportPlan:
    counts: dict[str, int]
    product_codes: set[str]
    duplicates: list[tuple[int, int, int]]


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
                    if field.primary_key or (
                        model is Price and field.name == "product"
                    ):
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


def validate_exports(paths: dict[str, Path]) -> ImportPlan:
    """Read without writing, keeping IDs rather than complete records in memory."""
    identifiers: dict[str, set[int]] = {}
    codes: set[str] = set()
    duplicates: list[tuple[int, int, int]] = []
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
                        raise CommandError(f"{prefix}: unknown {field} {reference}")
            if model is Price:
                if obj.product_code:
                    codes.add(obj.product_code)
                if obj.duplicate_of_id is not None:
                    duplicates.append((obj.pk, obj.duplicate_of_id, line))
        identifiers[name] = seen
    for pk, reference, line in duplicates:
        if reference == pk or reference not in identifiers["prices"]:
            raise CommandError(
                f"{paths['prices']}:{line}: invalid duplicate_of {reference}"
            )
    return ImportPlan(
        {name: len(ids) for name, ids in identifiers.items()}, codes, duplicates
    )


def require_empty_destination() -> None:
    for model in (Location, Proof, Price):
        if model._base_manager.exists():
            raise CommandError(
                f"{model._meta.db_table} is not empty. Use a fresh database; "
                "this command never merges or overwrites existing data."
            )


def insert_batch(
    model: type[models.Model], objects: list[Any], batch_size: int
) -> None:
    if model is Price:
        codes = {obj.product_code for obj in objects if obj.product_code}
        products = Product.objects.in_bulk(codes, field_name="code")
        Product.objects.bulk_create(
            [Product(code=code) for code in codes if code not in products],
            batch_size=batch_size,
        )
        products = Product.objects.in_bulk(codes, field_name="code")
        for obj in objects:
            obj.product_id = products[obj.product_code].pk if obj.product_code else None
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


def update_counts(
    target: Any, source: Any, foreign_key: str, counts: dict[str, Any]
) -> None:
    related = (
        source.filter(**{foreign_key: OuterRef("pk")}).order_by().values(foreign_key)
    )
    target.update(
        **{
            name: Coalesce(
                Subquery(related.annotate(value=expression).values("value")), 0
            )
            for name, expression in counts.items()
        }
    )


def rebuild_counts() -> None:
    update_counts(
        Proof.all_objects.all(),
        Price.objects.all(),
        "proof_id",
        {"price_count": Count("id")},
    )
    update_counts(
        Location.objects.all(),
        Price.objects.all(),
        "location_id",
        {
            "price_count": Count("id"),
            "product_count": Count("product_id", distinct=True),
        },
    )
    update_counts(
        Location.objects.all(),
        Proof.objects.all(),
        "location_id",
        {
            "proof_count": Count("id"),
            "user_count": Count("owner", distinct=True),
        },
    )
    zero_counts = dict.fromkeys(Product.COUNT_FIELDS, 0)
    Product.objects.exclude(**zero_counts).update(**zero_counts)
    products = Product.objects.filter(
        pk__in=Price.objects.exclude(product_id=None).values("product_id")
    )
    update_counts(
        products,
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
    )
    # Public exports contain owner names, not user accounts. Only update accounts
    # that already exist locally, using the application's existing calculations.
    User.update_task()
    TotalStats.update_task()
    # The public product manager can return an old PostgreSQL row estimate for
    # an unfiltered count when importing into an existing product catalog.
    TotalStats.objects.update(product_count=Product._base_manager.count())


def import_exports(
    paths: dict[str, Path], *, batch_size: int = 1000, dry_run: bool = False
) -> ImportPlan:
    if batch_size < 1:
        raise CommandError("batch_size must be positive")
    require_empty_destination()
    plan = validate_exports(paths)
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
            for name, model in (
                ("locations", Location),
                ("proofs", Proof),
                ("prices", Price),
            ):
                batch = []
                for _line, obj in read_objects(paths[name], model):
                    batch.append(obj)
                    if len(batch) == batch_size:
                        insert_batch(model, batch, batch_size)
                        batch = []
                if batch:
                    insert_batch(model, batch, batch_size)
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
