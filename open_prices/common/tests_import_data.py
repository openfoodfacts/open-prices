import gzip
import json
from contextlib import ExitStack
from datetime import UTC, date, datetime
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import DatabaseError, connection
from django.test import TestCase, override_settings

from open_prices.api.locations.serializers import LocationSerializer
from open_prices.api.prices.serializers import PriceSerializer
from open_prices.api.proofs.serializers import ProofSerializer
from open_prices.locations.models import Location
from open_prices.prices.models import Price
from open_prices.products.models import Product
from open_prices.proofs.models import Proof
from open_prices.stats.models import TotalStats
from open_prices.users.models import User


class ImportPublicDataTest(TestCase):
    created = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
    updated = datetime(2024, 2, 3, 4, 5, 6, tzinfo=UTC)
    existing_code = "8001505005707"
    new_code = "3017620422003"

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        timestamps = {"created": self.created, "updated": self.updated}
        locations = [
            Location(
                id=1001,
                type="OSM",
                osm_id=652825274,
                osm_type="NODE",
                osm_name="Example shop",
                osm_address_country="France",
                osm_address_country_code="fr",
                osm_lat=Decimal("48.1234567"),
                osm_lon=Decimal("2.1234567"),
                price_count=999,
                product_count=999,
                proof_count=999,
                user_count=999,
                **timestamps,
            ),
            Location(
                id=1002,
                type="ONLINE",
                website_url="https://example.org",
                **timestamps,
            ),
        ]
        proofs = [
            Proof(
                id=2001 + index,
                type=proof_type,
                location_id=location_id,
                owner=owner,
                currency="EUR",
                date=date(2024, 1, 1),
                file_path=f"2024/01/{index}.jpg",
                image_thumb_path=f"2024/01/{index}.400.jpg",
                receipt_price_total=Decimal("12.345") if index == 0 else None,
                price_count=999,
                prediction_count=999,
                **timestamps,
            )
            for index, (proof_type, location_id, owner) in enumerate(
                [
                    ("RECEIPT", 1001, "contributor-a"),
                    ("PRICE_TAG", 1001, "contributor-b"),
                    ("SHOP_IMPORT", 1002, "contributor-a"),
                ]
            )
        ]
        prices = [
            Price(
                id=3001,
                type="PRODUCT",
                product_code=self.existing_code,
                product_id=99001,
                location_id=1001,
                proof_id=2001,
                duplicate_of_id=3004,
                price=Decimal("1.239"),
                receipt_quantity=Decimal("1.125"),
                owner="contributor-a",
                **timestamps,
            ),
            Price(
                id=3002,
                type="CATEGORY",
                category_tag="en:apples",
                labels_tags=["en:organic"],
                origins_tags=["en:france"],
                location_id=1001,
                proof_id=2001,
                price=Decimal("2.345"),
                price_per="KILOGRAM",
                owner="contributor-a",
                **timestamps,
            ),
            Price(
                id=3003,
                type="PRODUCT",
                product_code=self.new_code,
                product_id=99002,
                location_id=1001,
                proof_id=2002,
                price=Decimal("3.456"),
                owner="contributor-b",
                **timestamps,
            ),
            Price(
                id=3004,
                type="PRODUCT",
                product_code=self.existing_code,
                product_id=99001,
                location_id=1002,
                proof_id=2003,
                price=Decimal("4.567"),
                owner="contributor-a",
                **timestamps,
            ),
        ]
        for price in prices:
            price.currency = "EUR"
            price.date = date(2024, 1, 1)
        self.rows = {
            "locations": list(LocationSerializer(locations, many=True).data),
            "proofs": list(ProofSerializer(proofs, many=True).data),
            "prices": list(PriceSerializer(prices, many=True).data),
        }
        # Future export metadata must not be passed to model constructors.
        self.rows["locations"][0]["export_metadata"] = {"version": 1}
        self.paths = {name: self.directory / f"{name}.jsonl" for name in self.rows}
        self.write_exports()

    def write_exports(self):
        for name, rows in self.rows.items():
            path = self.paths[name]
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "wt", encoding="utf-8") as stream:
                for row in rows:
                    stream.write(json.dumps(row, cls=DjangoJSONEncoder) + "\n")

    def run_import(self, **options):
        output = StringIO()
        call_command(
            "import_public_data",
            **{name: str(path) for name, path in self.paths.items()},
            batch_size=2,
            stdout=output,
            **options,
        )
        return output.getvalue()

    def assert_no_imported_rows(self):
        self.assertFalse(Location.objects.exists())
        self.assertFalse(Proof.all_objects.exists())
        self.assertFalse(Price.objects.exists())
        self.assertFalse(Product.objects.exists())
        self.assertFalse(TotalStats.objects.exists())

    def assert_source_error(self, name, line):
        with self.assertRaises(CommandError) as caught:
            self.run_import()
        message = str(caught.exception)
        self.assertIn(self.paths[name].name, message)
        self.assertRegex(message, rf"(?::|line\s+){line}\b")
        self.assert_no_imported_rows()

    @override_settings(TESTING=False, ENABLE_OCR=True, ENABLE_ML_PREDICTIONS=True)
    def test_imports_serializer_exports_without_model_saves_or_background_tasks(self):
        existing_product = Product(
            code=self.existing_code,
            product_name="Existing catalog name",
            categories_tags=["en:chocolates"],
        )
        Product.objects.bulk_create([existing_product])
        User.objects.bulk_create([User(user_id="contributor-a")])
        with ExitStack() as stack:
            saves = [
                stack.enter_context(
                    patch.object(model, "save", side_effect=AssertionError("save"))
                )
                for model in (Location, Proof, Price, Product)
            ]
            tasks = [
                stack.enter_context(patch(f"open_prices.{app}.models.async_task"))
                for app in ("locations", "proofs", "prices", "products")
            ]
            self.run_import()
            for mocked in saves + tasks:
                mocked.assert_not_called()

        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Proof.all_objects.count(), 3)
        self.assertEqual(Price.objects.count(), 4)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(User.objects.count(), 1)
        existing_product.refresh_from_db()
        self.assertEqual(existing_product.product_name, "Existing catalog name")
        self.assertEqual(existing_product.categories_tags, ["en:chocolates"])
        for field, expected in {
            "price_count": 2,
            "price_currency_count": 1,
            "location_count": 2,
            "location_type_osm_country_count": 1,
            "user_count": 1,
            "proof_count": 2,
        }.items():
            self.assertEqual(getattr(existing_product, field), expected, field)
        placeholder = Product.objects.get(code=self.new_code)
        self.assertEqual(placeholder.price_count, 1)

        first = Price.objects.get(pk=3001)
        self.assertEqual(first.product_id, existing_product.pk)
        self.assertEqual(first.duplicate_of_id, 3004)
        self.assertEqual(first.price, Decimal("1.239"))
        self.assertEqual(first.receipt_quantity, Decimal("1.125"))
        self.assertEqual(Price.objects.get(pk=3003).product_id, placeholder.pk)
        category = Price.objects.get(pk=3002)
        self.assertIsNone(category.product_id)
        self.assertEqual(category.category_tag, "en:apples")
        self.assertEqual(category.labels_tags, ["en:organic"])
        self.assertEqual(category.origins_tags, ["en:france"])

        location = Location.objects.get(pk=1001)
        self.assertEqual(location.osm_lat, Decimal("48.1234567"))
        self.assertEqual(location.price_count, 3)
        self.assertEqual(location.product_count, 2)
        self.assertEqual(location.proof_count, 2)
        self.assertEqual(location.user_count, 2)
        proof = Proof.objects.get(pk=2001)
        self.assertEqual(proof.location_id, location.pk)
        self.assertEqual(proof.receipt_price_total, Decimal("12.345"))
        self.assertEqual(proof.price_count, 2)
        self.assertEqual(proof.prediction_count, 0)
        self.assertEqual(proof.file_path, "2024/01/0.jpg")
        for queryset in (
            Location.objects.all(),
            Proof.all_objects.all(),
            Price.objects.all(),
        ):
            for instance in queryset:
                self.assertEqual(instance.created, self.created)
                self.assertEqual(instance.updated, self.updated)
        stats = TotalStats.objects.get()
        for field, expected in {
            "price_count": 4,
            "price_type_product_code_count": 3,
            "price_type_category_tag_count": 1,
            "location_count": 2,
            "location_with_price_count": 2,
            "proof_count": 3,
            "proof_with_price_count": 3,
            "product_count": 2,
            "product_with_price_count": 2,
        }.items():
            self.assertEqual(getattr(stats, field), expected, field)

    def test_reads_gzip_exports_and_resets_primary_key_sequences(self):
        self.paths = {name: self.directory / f"{name}.jsonl.gz" for name in self.rows}
        self.write_exports()
        self.run_import()
        for model, instance, maximum_id in (
            (
                Location,
                Location(type="ONLINE", website_url="https://example.net"),
                1002,
            ),
            (Proof, Proof(type="PRICE_TAG"), 2003),
            (Price, Price(type="CATEGORY", category_tag="en:apples"), 3004),
        ):
            model.objects.bulk_create([instance])
            self.assertGreater(instance.pk, maximum_id)

    def test_total_product_count_ignores_stale_postgresql_estimates(self):
        Product.objects.bulk_create([Product(code=self.existing_code)])
        try:
            with connection.cursor() as cursor:
                cursor.execute("ANALYZE products")
            self.assertEqual(Product.objects.count(), 1)

            self.run_import()

            self.assertEqual(Product._base_manager.count(), 2)
            self.assertEqual(TotalStats.objects.get().product_count, 2)
        finally:
            # ANALYZE statistics survive rollback; restore an empty estimate so
            # later tests can use the manager's exact-count fallback.
            Product._base_manager.all().delete()
            with connection.cursor() as cursor:
                cursor.execute("ANALYZE products")

    def test_dry_run_validates_without_writing(self):
        self.run_import(dry_run=True)
        self.assert_no_imported_rows()

    def test_dry_run_rejects_dangling_references(self):
        self.rows["prices"][3]["proof_id"] = 99999
        self.write_exports()
        with self.assertRaises(CommandError):
            self.run_import(dry_run=True)
        self.assert_no_imported_rows()

    def test_refuses_repeated_import_without_changing_existing_data(self):
        self.run_import()
        before = list(Price.objects.order_by("pk").values())
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(list(Price.objects.order_by("pk").values()), before)
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Proof.all_objects.count(), 3)

    def test_refuses_database_containing_only_a_draft_proof(self):
        proof = Proof(type="RECEIPT", draft=True)
        Proof.all_objects.bulk_create([proof])
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(Proof.all_objects.get().pk, proof.pk)
        self.assertFalse(Location.objects.exists())
        self.assertFalse(Price.objects.exists())

    def test_malformed_json_rolls_back_preceding_batches(self):
        with self.paths["prices"].open("a", encoding="utf-8") as stream:
            stream.write("{malformed json\n")
        self.assert_source_error("prices", 5)

    def test_duplicate_source_id_across_batches_is_rejected(self):
        self.rows["prices"].append(dict(self.rows["prices"][0]))
        self.write_exports()
        self.assert_source_error("prices", 5)

    def test_failed_import_preserves_existing_catalog_data_and_counters(self):
        product = Product(
            code=self.existing_code,
            product_name="Existing catalog name",
            price_count=17,
        )
        Product.objects.bulk_create([product])
        before = Product.objects.values().get(pk=product.pk)
        with self.paths["prices"].open("a", encoding="utf-8") as stream:
            stream.write("{malformed json\n")
        with self.assertRaises(CommandError):
            self.run_import()
        self.assertEqual(Product.objects.values().get(pk=product.pk), before)
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(Location.objects.exists())
        self.assertFalse(Proof.all_objects.exists())
        self.assertFalse(Price.objects.exists())

    def test_database_error_after_insertion_rolls_back_all_changes(self):
        product = Product(code=self.existing_code, price_count=17)
        Product.objects.bulk_create([product])
        before = Product.objects.values().get(pk=product.pk)

        def fail_after_insertion():
            self.assertEqual(Location.objects.count(), 2)
            self.assertEqual(Proof.all_objects.count(), 3)
            self.assertEqual(Price.objects.count(), 4)
            self.assertEqual(Product.objects.count(), 2)
            Product.objects.filter(pk=product.pk).update(price_count=999)
            raise DatabaseError("Counter update failed")

        with (
            patch(
                "open_prices.common.data_import.rebuild_counts",
                side_effect=fail_after_insertion,
            ),
            self.assertRaises(CommandError),
        ):
            self.run_import()

        self.assertEqual(Product.objects.values().get(pk=product.pk), before)
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(Location.objects.exists())
        self.assertFalse(Proof.all_objects.exists())
        self.assertFalse(Price.objects.exists())
        self.assertFalse(TotalStats.objects.exists())

    def test_dangling_price_references_are_rejected(self):
        for field in ("location_id", "proof_id", "duplicate_of"):
            with self.subTest(field=field):
                original = self.rows["prices"][3][field]
                self.rows["prices"][3][field] = 99999
                self.write_exports()
                self.assert_source_error("prices", 4)
                self.rows["prices"][3][field] = original

    def test_dangling_proof_location_is_rejected(self):
        self.rows["proofs"][2]["location_id"] = 99999
        self.write_exports()
        self.assert_source_error("proofs", 3)

    def test_invalid_batch_size_is_rejected(self):
        with self.assertRaises(CommandError):
            call_command(
                "import_public_data",
                **{name: str(path) for name, path in self.paths.items()},
                batch_size=0,
                stdout=StringIO(),
            )
        self.assert_no_imported_rows()
