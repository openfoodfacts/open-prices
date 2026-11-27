import datetime
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from openfoodfacts import APIVersion, Flavor
from openfoodfacts.redis import ProductUpdateEvent

from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.products import constants as product_constants
from open_prices.products.factories import ProductFactory
from open_prices.products.management.commands.run_update_listener import (
    UpdateListener,
)
from open_prices.products.models import Product
from open_prices.products.tasks import (
    fetch_and_save_data_from_openfoodfacts,
    process_update,
)
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import UserFactory

UPDATE_LISTENER_MODULE = "open_prices.products.management.commands.run_update_listener"

PRODUCT_OFF = {
    "code": "3017620425035",
    "price_count": 11,
    "source": product_constants.SOURCE_OFF,
    "product_name": "Nutella",
    "product_quantity": 1000,
    "product_quantity_unit": "g",
    "quantity": "1 kg",
    "categories_tags": [
        "en:breakfasts",
        "en:fats",
        "en:spreads",
        "en:sweet-spreads",
        "fr:pates-a-tartiner",
        "en:hazelnut-spreads",
        "en:chocolate-spreads",
        "en:cocoa-and-hazelnuts-spreads",
    ],
    "brands": "Ferrero",
    "brands_tags": ["ferrero"],
    "labels_tags": [
        "en:no-gluten",
        "en:no-preservatives",
        "en:no-colorings",
        "en:no-hydrogenated-fats",
        "fr:triman",
        "fr:sgs",
    ],
    "image_url": "https://images.openfoodfacts.org/images/products/301/762/042/5035/front_en.488.400.jpg",
    "nutriscore_grade": "e",
    "ecoscore_grade": "d",
    "nova_group": 4,
    "creator": "openfoodfacts-contributors",
    "unique_scans_n": 1051,
}

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
    "osm_address_city": "Grenoble",
    "osm_address_country": "France",
    "price_count": 15,
}
LOCATION_ONLINE_DECATHLON = {
    "type": location_constants.TYPE_ONLINE,
    "website_url": "https://www.decathlon.fr",
    "price_count": 15,
}


class ProductModelSaveTest(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_product_validation(self):
        # code & source
        ProductFactory(code="0123456789101")
        self.assertRaises(ValidationError, ProductFactory, code=None)
        self.assertRaises(ValidationError, ProductFactory, code="")
        self.assertRaises(
            ValidationError, ProductFactory, code="0123456789101"
        )  # duplicate
        ProductFactory(code="0123456789102", source=product_constants.SOURCE_OFF)
        self.assertRaises(
            ValidationError, ProductFactory, code="0123456789102", source="test"
        )
        # categories_tags
        ProductFactory(code="0123456789103", categories_tags=None)
        ProductFactory(code="0123456789104", categories_tags=[])
        ProductFactory(code="0123456789105", categories_tags=["test"])
        # unique_scan_n
        ProductFactory(code="0123456789106", unique_scans_n=None)
        # full OFF object
        ProductFactory(**PRODUCT_OFF)

    def test_code_normalization_on_save(self):
        # barcode of length 12 gets padded to 13
        product = ProductFactory(code="123456789100")
        self.assertEqual(product.code, "0123456789100")
        # barcode of length 14 with leading zero gets trimmed to 13
        product = ProductFactory(code="00123456789101")
        self.assertEqual(product.code, "0123456789101")
        # EAN8 without leading 0 stays the same
        product = ProductFactory(code="51234567")
        self.assertEqual(product.code, "51234567")
        # barcode of length < 8 gets padded to 8
        product = ProductFactory(code="4567")
        self.assertEqual(product.code, "00004567")
        # barcode of length > 13 without leading 0 stays the same
        product = ProductFactory(code="8658585456785867")
        self.assertEqual(product.code, "8658585456785867")


class ProductQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product_without_price = ProductFactory(
            code="0123456789100", creator=settings.OFF_DEFAULT_USER
        )
        cls.product_with_price = ProductFactory(
            code="0123456789101", creator="openfoodfacts-contributors"
        )
        PriceFactory(product_code=cls.product_with_price.code, price=1.0)

    def test_has_prices(self):
        self.assertEqual(Product.objects.has_prices().count(), 1)

    def test_created_by_open_prices(self):
        self.assertEqual(Product.objects.created_by_open_prices().count(), 1)

    def test_with_stats(self):
        product = Product.objects.with_stats().get(id=self.product_without_price.id)
        self.assertEqual(product.price_count_annotated, 0)
        self.assertEqual(product.price_count, 0)
        product = Product.objects.with_stats().get(id=self.product_with_price.id)
        self.assertEqual(product.price_count_annotated, 1)
        self.assertEqual(product.price_count, 1)

    def test_to_update_in_sync_task(self):
        ProductFactory(code="0123456789102", source=Flavor.off)
        ProductFactory(code="0123456789103", source=Flavor.obf)
        self.assertEqual(
            set(
                Product.objects.to_update_in_sync_task(
                    codes=[
                        # no source (created in Open Prices before OFF)
                        self.product_without_price.code,
                        # same flavor
                        "0123456789102",
                        # other flavor
                        "0123456789103",
                    ],
                    flavor=Flavor.off,
                ).values_list("code", flat=True)
            ),
            {self.product_without_price.code, "0123456789102"},
        )


class ProductPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(code="0123456789100", product_quantity=1000)
        cls.user = UserFactory()
        cls.location_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_2 = LocationFactory(**LOCATION_ONLINE_DECATHLON)
        cls.proof = ProofFactory(
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            currency="EUR",
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code=cls.product.code,
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            proof_id=cls.proof.id,
            price=1.0,
            currency=cls.proof.currency,
            price_is_discounted=True,
            price_without_discount=1.5,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code=cls.product.code,
            location_osm_id=cls.location_2.osm_id,
            location_osm_type=cls.location_2.osm_type,
            price=2.0,
            currency="USD",
            owner=cls.user.user_id,
        )

    def test_with_counts_fields(self):
        self.assertEqual(
            set(Product.objects.with_counts().query.annotations),
            {f"{field}_annotated" for field in Product.COUNT_FIELDS},
        )

    def test_with_counts(self):
        product = Product.objects.with_counts().get(id=self.product.id)
        self.assertEqual(product.price_count_annotated, 2)
        self.assertEqual(product.price_currency_count_annotated, 2)
        self.assertEqual(product.location_count_annotated, 1)  # online: no location
        self.assertEqual(product.location_type_osm_country_count_annotated, 1)
        self.assertEqual(product.user_count_annotated, 1)
        self.assertEqual(product.proof_count_annotated, 1)
        product_without_price = ProductFactory(code="0123456789101")
        product = Product.objects.with_counts().get(id=product_without_price.id)
        self.assertEqual(product.price_count_annotated, 0)
        self.assertEqual(product.proof_count_annotated, 0)

    def test_update_task(self):
        product_without_price = ProductFactory(code="0123456789101")
        product_with_deleted_prices = ProductFactory(code="0123456789102")
        PriceFactory(
            product_code=product_with_deleted_prices.code,
            price=3.0,
            owner=self.user.user_id,
        )
        Product.update_task()
        # the price post_delete signal only decrements price_count
        product_with_deleted_prices.prices.all().delete()
        product_with_deleted_prices.refresh_from_db()
        self.assertEqual(product_with_deleted_prices.price_count, 0)
        self.assertEqual(product_with_deleted_prices.user_count, 1)  # stale
        # wrong counts
        Product.objects.filter(id=self.product.id).update(
            **{field: 99 for field in Product.COUNT_FIELDS}
        )
        # update_task() should fix all counts
        updated_count = Product.update_task()
        self.assertEqual(updated_count, 2)
        self.assertFalse(  # skipped
            Product.objects.for_update_task()
            .filter(id=product_without_price.id)
            .exists()
        )
        self.product.refresh_from_db()
        self.assertEqual(
            {field: getattr(self.product, field) for field in Product.COUNT_FIELDS},
            {
                "price_count": 2,
                "price_currency_count": 2,
                "location_count": 1,
                "location_type_osm_country_count": 1,
                "user_count": 1,
                "proof_count": 1,
            },
        )
        product_with_deleted_prices.refresh_from_db()
        self.assertEqual(
            {
                getattr(product_with_deleted_prices, field)
                for field in Product.COUNT_FIELDS
            },
            {0},
        )
        # nothing to update anymore
        self.assertEqual(Product.update_task(), 0)

    def test_update_counts(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.price_count, 2)  # price signals
        self.assertEqual(self.product.proof_count, 0)
        # update_counts() should fix all counts
        self.product.update_counts()
        self.product.refresh_from_db()
        self.assertEqual(
            {field: getattr(self.product, field) for field in Product.COUNT_FIELDS},
            {
                "price_count": 2,
                "price_currency_count": 2,
                "location_count": 1,  # online: no location
                "location_type_osm_country_count": 1,
                "user_count": 1,
                "proof_count": 1,
            },
        )
        # bulk delete prices to skip signals
        self.product.prices.all().delete()
        self.product.update_counts()
        self.product.refresh_from_db()
        self.assertEqual(
            {getattr(self.product, field) for field in Product.COUNT_FIELDS}, {0}
        )

    def test_price__min(self):
        self.assertEqual(self.product.price__min(), 1.0)
        self.assertEqual(self.product.price__min(exclude_discounted=True), 2.0)

    def test_price__max(self):
        self.assertEqual(self.product.price__max(), 2.0)
        self.assertEqual(self.product.price__max(exclude_discounted=True), 2.0)

    def test_price__avg(self):
        self.assertEqual(self.product.price__avg(), 1.5)
        self.assertEqual(self.product.price__avg(exclude_discounted=True), 2.0)

    def test_price__stats(self):
        self.assertEqual(
            self.product.price__stats(),
            {
                "price__count": 2,
                "price__min": Decimal("1.0"),
                "price__max": Decimal("2.0"),
                "price__avg": Decimal("1.50"),
                "proof__count": 1,
            },
        )
        self.assertEqual(
            self.product.price__stats(exclude_discounted=True),
            {
                "price__count": 1,
                "price__min": Decimal("2.0"),
                "price__max": Decimal("2.0"),
                "price__avg": Decimal("2.00"),
                "proof__count": 0,
            },
        )


class TestProcessUpdate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(code="0123456789100")

    @classmethod
    def tearDownClass(cls):
        Product.objects.all().delete()
        super().tearDownClass()

    @patch("open_prices.common.openfoodfacts.get_product")
    def test_process_update_product_exists(self, mock_get_product):
        product_details = {
            "product_name": "Test Product",
            "code": self.product.code,
            "image_url": "https://images.openfoodfacts.org/images/products/123/1.jpg",
            "product_quantity": 1000,
            "product_quantity_unit": "g",
            "quantity": "1 kg",
            "categories_tags": ["en:apples"],
            "creator": "openfoodfacts-contributors",
            "unique_scans_n": 42,
            "misc_tags": ["en:nutriscore-computed"],
        }
        fields_to_ignore = ["misc_tags"]
        mock_get_product.return_value = product_details

        before = timezone.now()
        process_update(self.product.code, Flavor.obf)
        after = timezone.now()

        updated_product = Product.objects.get(code=self.product.code)
        for key, value in product_details.items():
            if key in fields_to_ignore:
                self.assertNotIn(key, updated_product.__dict__)
            else:
                self.assertEqual(getattr(updated_product, key), value)

        self.assertEqual(updated_product.source, Flavor.obf)
        self.assertGreater(updated_product.source_last_synced, before)
        self.assertLess(updated_product.source_last_synced, after)

    @patch("open_prices.common.openfoodfacts.get_product")
    def test_process_update_new_product(self, mock_get_product):
        # create a new product
        code = "1234567891011"
        product_details = {
            "product_name": "Test Product",
            "code": code,
            "image_url": "https://images.openfoodfacts.org/images/products/123/1.jpg",
            "product_quantity": 1000,
            "product_quantity_unit": "g",
            "quantity": "1 kg",
            "categories_tags": ["en:apples"],
            "creator": "openfoodfacts-contributors",
            "unique_scans_n": 42,
            "misc_tags": ["en:nutriscore-computed"],
        }
        fields_to_ignore = ["misc_tags"]
        mock_get_product.return_value = product_details

        before = timezone.now()
        process_update(code, Flavor.opff)
        after = timezone.now()

        results = Product.objects.filter(code=code)
        self.assertEqual(results.count(), 1)
        create_product = results.first()

        for key, value in product_details.items():
            if key in fields_to_ignore:
                self.assertNotIn(key, create_product.__dict__)
            else:
                self.assertEqual(getattr(create_product, key), value)

        self.assertEqual(create_product.source, Flavor.opff)
        self.assertGreater(create_product.source_last_synced, before)
        self.assertLess(create_product.source_last_synced, after)

    @patch("open_prices.common.openfoodfacts.get_product")
    def test_process_update_resets_missing_fields(self, mock_get_product):
        # e.g. a food product moved to OBF: the food fields are gone
        code = "1234567891012"
        ProductFactory(
            code=code,
            source=Flavor.off,
            categories_tags=["en:apples"],
            nutriscore_grade="a",
            nova_group=1,
            unique_scans_n=42,
        )
        mock_get_product.return_value = {"code": code, "product_name": "Shampoo"}

        process_update(code, Flavor.obf)

        product = Product.objects.get(code=code)
        self.assertEqual(product.product_name, "Shampoo")
        self.assertEqual(product.source, Flavor.obf)
        self.assertEqual(product.categories_tags, [])
        self.assertIsNone(product.nutriscore_grade)
        self.assertIsNone(product.nova_group)
        self.assertEqual(product.unique_scans_n, 0)


class FetchAndSaveDataFromOpenFoodFactsTest(TestCase):
    @patch("open_prices.common.openfoodfacts.get_product")
    def test_fetch_does_not_overwrite_counts(self, mock_get_product):
        product = ProductFactory(code="0123456789100")
        # the task receives the product instance as it was at creation
        stale_product = Product.objects.get(id=product.id)
        # meanwhile, a price is added (see price_post_create_increment_counts)
        Product.objects.filter(id=product.id).update(price_count=1)
        mock_get_product.return_value = {
            "code": product.code,
            "product_name": "Test Product",
        }

        fetch_and_save_data_from_openfoodfacts(stale_product)

        product.refresh_from_db()
        self.assertEqual(product.product_name, "Test Product")
        self.assertEqual(product.source, Flavor.off)
        self.assertEqual(product.price_count, 1)


class UpdateListenerTest(TestCase):
    def setUp(self):
        self.listener = UpdateListener(
            redis_client=None,
            redis_latest_id_key="test",
            product_updates_stream_name="product_updates",
        )

    def build_event(self, action: str) -> ProductUpdateEvent:
        return ProductUpdateEvent(
            id="1700000000000-0",
            stream="product_updates",
            # old event: no 2s wait before processing
            timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
            code="0123456789100",
            flavor="off",
            user_id="test",
            action=action,
            comment="",
            product_type="beauty",
        )

    @patch(f"{UPDATE_LISTENER_MODULE}.process_delete")
    @patch(f"{UPDATE_LISTENER_MODULE}.process_update")
    def test_process_redis_update(self, mock_process_update, mock_process_delete):
        for action in ["created", "updated"]:
            with self.subTest(action=action):
                mock_process_update.reset_mock()
                self.listener.process_redis_update(self.build_event(action))
                mock_process_update.assert_called_once_with("0123456789100", Flavor.obf)
                mock_process_delete.assert_not_called()
        with self.subTest(action="deleted"):
            mock_process_update.reset_mock()
            self.listener.process_redis_update(self.build_event("deleted"))
            mock_process_delete.assert_called_once_with("0123456789100", Flavor.obf)
            mock_process_update.assert_not_called()
        with self.subTest(action="archived"):
            mock_process_delete.reset_mock()
            self.listener.process_redis_update(self.build_event("archived"))
            mock_process_update.assert_not_called()
            mock_process_delete.assert_not_called()


class GetProductTest(TestCase):
    @patch("open_prices.common.openfoodfacts.API")
    def test_get_product_only_requests_needed_fields(self, mock_api):
        common_openfoodfacts.get_product("0123456789100", Flavor.obf)

        # API v3.5: same product schema as the JSONL exports
        self.assertEqual(mock_api.call_args.kwargs["version"], APIVersion.v3_5)
        mock_api.return_value.product.get.assert_called_once_with(
            "0123456789100", fields=common_openfoodfacts.OFF_API_FIELDS
        )
        # renamed fields are requested with their recent name
        self.assertIn("environmental_score_grade", common_openfoodfacts.OFF_API_FIELDS)
        self.assertNotIn("ecoscore_grade", common_openfoodfacts.OFF_API_FIELDS)

    @patch("open_prices.common.openfoodfacts.API")
    def test_get_product_dict_not_found(self, mock_api):
        # the OFF API v3.5 returns a 404 for unknown & invalid barcodes
        # (the openfoodfacts library then returns None)
        mock_api.return_value.product.get.return_value = None

        self.assertEqual(common_openfoodfacts.get_product_dict("0123456789100"), {})


class BuildProductDictTest(TestCase):
    def test_build_product_dict_environmental_score_grade(self):
        # recent product schema (API v3.5 & JSONL exports)
        product_dict = common_openfoodfacts.build_product_dict(
            {"code": "0123456789100", "environmental_score_grade": "b"}, Flavor.off
        )
        self.assertEqual(product_dict["ecoscore_grade"], "b")
        self.assertNotIn("environmental_score_grade", product_dict)
        # both names: the recent one wins
        product_dict = common_openfoodfacts.build_product_dict(
            {
                "code": "0123456789100",
                "ecoscore_grade": "c",
                "environmental_score_grade": "b",
            },
            Flavor.off,
        )
        self.assertEqual(product_dict["ecoscore_grade"], "b")

    def test_build_product_dict_ecoscore_grade(self):
        # old product schema
        product_dict = common_openfoodfacts.build_product_dict(
            {"code": "0123456789100", "ecoscore_grade": "c"}, Flavor.off
        )
        self.assertEqual(product_dict["ecoscore_grade"], "c")
        # missing: reset to the default value
        product_dict = common_openfoodfacts.build_product_dict(
            {"code": "0123456789100"}, Flavor.off
        )
        self.assertIsNone(product_dict["ecoscore_grade"])

    def test_build_product_dict_brands_tags(self):
        # brands_tags are kept as is (with the "xx:" prefix in the recent schema)
        product_dict = common_openfoodfacts.build_product_dict(
            {
                "code": "0123456789100",
                "brands": "Albert Heijn",
                "brands_tags": ["xx:albert-heijn"],
            },
            Flavor.off,
        )
        self.assertEqual(product_dict["brands_tags"], ["xx:albert-heijn"])


class TestProductModel(TestCase):
    def test_fuzzy_barcode_search(self):
        ProductFactory(code="0123456789100")
        ProductFactory(code="0123456789101")
        ProductFactory(code="0123456789102")
        ProductFactory(code="0123456789103")
        ProductFactory(code="1123456789100")
        ProductFactory(code="1123456789101")
        ProductFactory(code="1123456789102")
        ProductFactory(code="1123456789103")
        ProductFactory(code="2123456789100")
        ProductFactory(code="2123456789101")
        ProductFactory(code="2123456789102")
        ProductFactory(code="2123456789103")

        results = list(
            Product.objects.fuzzy_barcode_search(
                "0123456789100", max_distance=0, exclude_distance_0=False
            )
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].code, "0123456789100")

        results = list(
            Product.objects.fuzzy_barcode_search(
                "0123456789100", max_distance=1, exclude_distance_0=False
            )
        )
        self.assertEqual(len(results), 6)
        self.assertEqual(
            set(p.code for p in results),
            {
                "0123456789100",
                "0123456789101",
                "0123456789102",
                "0123456789103",
                "1123456789100",
                "2123456789100",
            },
        )

        results = list(
            Product.objects.fuzzy_barcode_search(
                "0123456789100", max_distance=2, exclude_distance_0=False
            )
        )
        self.assertEqual(len(results), 12)

        results = list(
            Product.objects.fuzzy_barcode_search(
                "0123456789100", max_distance=3, exclude_distance_0=True
            )
        )
        self.assertEqual(len(results), 11)
