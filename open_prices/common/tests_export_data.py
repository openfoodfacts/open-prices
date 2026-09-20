import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.cache import cache
from django.test import TestCase, override_settings

from open_prices.common.export_data import export_public_data
from open_prices.common.import_data import import_exports
from open_prices.common.tasks import dump_db_task
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof

EXPORT_NAMES = ("locations", "proofs", "prices")


def read_jsonl_gz(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class ExportPublicDataTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = LocationFactory()
        cls.proof = ProofFactory(
            location_osm_id=cls.location.osm_id, location_osm_type=cls.location.osm_type
        )
        cls.prices = PriceFactory.create_batch(
            2,
            proof=cls.proof,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
        )

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base_dir = Path(directory.name)
        settings_override = override_settings(BASE_DIR=self.base_dir)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.data_dir = self.base_dir / "data"

    def test_export_writes_one_gzip_jsonl_file_per_table(self):
        export_public_data()

        for name, expected_ids in (
            ("locations", {self.location.pk}),
            ("proofs", {self.proof.pk}),
            ("prices", {price.pk for price in self.prices}),
        ):
            rows = read_jsonl_gz(self.data_dir / f"{name}.jsonl.gz")
            self.assertEqual({row["id"] for row in rows}, expected_ids)

    def test_export_replaces_the_previous_files(self):
        export_public_data()
        Price.objects.filter(pk=self.prices[0].pk).delete()
        export_public_data()

        rows = read_jsonl_gz(self.data_dir / "prices.jsonl.gz")
        self.assertEqual([row["id"] for row in rows], [self.prices[1].pk])

    def test_dump_db_task_exports_the_public_data(self):
        dump_db_task()

        for name in EXPORT_NAMES:
            self.assertTrue((self.data_dir / f"{name}.jsonl.gz").is_file())

    def test_exports_can_be_imported_back(self):
        export_public_data()
        expected = {
            model: list(model._base_manager.order_by("pk").values("pk"))
            for model in (Location, Proof, Price)
        }
        Price.objects.all().delete()
        Proof.all_objects.all().delete()
        Location.objects.all().delete()

        plan = import_exports(
            {name: self.data_dir / f"{name}.jsonl.gz" for name in EXPORT_NAMES}
        )

        self.assertEqual(plan.counts, {"locations": 1, "proofs": 1, "prices": 2})
        for model, rows in expected.items():
            self.assertEqual(
                list(model._base_manager.order_by("pk").values("pk")), rows
            )
