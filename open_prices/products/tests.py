from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from openfoodfacts import Flavor

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.products import constants as product_constants
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product
from open_prices.products.tasks import process_update
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import UserFactory

PRODUCT_OFF = {
    "code": "3017620425035",
    "price_count": 11,
    "source": product_constants.SOURCE_OFF,
    "product_name": "Nutella",
    "product_quantity": 1000,
    "product_quantity_unit": "g",
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


class ProductQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product_without_price = ProductFactory(code="0123456789100")
        cls.product_with_price = ProductFactory(code="0123456789101")
        PriceFactory(product_code=cls.product_with_price.code, price=1.0)

    def test_has_prices(self):
        self.assertEqual(Product.objects.has_prices().count(), 1)

    def test_with_stats(self):
        product = Product.objects.with_stats().get(id=self.product_without_price.id)
        self.assertEqual(product.price_count_annotated, 0)
        self.assertEqual(product.price_count, 0)
        product = Product.objects.with_stats().get(id=self.product_with_price.id)
        self.assertEqual(product.price_count_annotated, 1)
        self.assertEqual(product.price_count, 1)


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
            },
        )
        self.assertEqual(
            self.product.price__stats(exclude_discounted=True),
            {
                "price__count": 1,
                "price__min": Decimal("2.0"),
                "price__max": Decimal("2.0"),
                "price__avg": Decimal("2.00"),
            },
        )

    def test_update_price_count(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.price_count, 2)  # price signals
        self.assertEqual(self.product.price_currency_count, 0)
        # update_price_count() should fix price counts
        self.product.update_price_count()
        self.assertEqual(self.product.price_count, 2)
        self.assertEqual(self.product.price_currency_count, 2)
        # bulk delete prices to skip signals
        self.product.prices.all().delete()
        self.assertEqual(self.product.price_count, 2)  # should be 0
        self.assertEqual(self.product.price_currency_count, 2)  # should be 0
        # update_price_count() should fix price counts
        self.product.update_price_count()
        self.assertEqual(self.product.price_count, 0)  # all deleted
        self.assertEqual(self.product.price_currency_count, 0)

    def test_update_location_count(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.location_count, 0)
        self.assertEqual(self.product.location_type_osm_country_count, 0)
        # update_location_count() should fix location counts
        self.product.update_location_count()
        self.assertEqual(self.product.location_count, 1)
        self.assertEqual(self.product.location_type_osm_country_count, 1)

    def test_update_user_count(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.user_count, 0)
        # update_user_count() should fix user counts
        self.product.update_user_count()
        self.assertEqual(self.product.user_count, 1)

    def test_update_proof_count(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.proof_count, 0)
        # update_proof_count() should fix proof counts
        self.product.update_proof_count()
        self.assertEqual(self.product.proof_count, 1)


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
            "categories_tags": ["en:apples"],
            "unique_scans_n": 42,
            "owner": "test",
        }
        fields_to_ignore = ["owner"]
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
            "categories_tags": ["en:apples"],
            "unique_scans_n": 42,
            "owner": "test",
        }
        fields_to_ignore = ["owner"]
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

        results = list(Product.fuzzy_barcode_search("0123456789100", max_distance=0))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].code, "0123456789100")

        results = list(Product.fuzzy_barcode_search("0123456789100", max_distance=1))
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

        results = list(Product.fuzzy_barcode_search("0123456789100", max_distance=2))
        self.assertEqual(len(results), 12)
