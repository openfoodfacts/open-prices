from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase

from open_prices.prices.factories import PriceFactory
from open_prices.products import constants as product_constants
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product

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
        PriceFactory(
            product_code=cls.product.code,
            price=1.0,
            price_is_discounted=True,
            price_without_discount=1.5,
        )
        PriceFactory(product_code=cls.product.code, price=2.0)

    def test_update_price_count(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.price_count, 2)
        # bulk delete prices to skip signals
        self.product.prices.all().delete()
        self.assertEqual(self.product.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.product.update_price_count()
        self.assertEqual(self.product.price_count, 0)

    def test_price_min(self):
        self.assertEqual(self.product.price_min(), 1.0)
        self.assertEqual(self.product.price_min(exclude_discounted=True), 2.0)

    def test_price_max(self):
        self.assertEqual(self.product.price_max(), 2.0)

    def test_price_avg(self):
        self.assertEqual(self.product.price_avg(), 1.5)
        self.assertEqual(self.product.price_avg(exclude_discounted=True), 2.0)

    def test_price_stats(self):
        self.assertEqual(
            self.product.price_stats(),
            {
                "price__count": 2,
                "price__min": Decimal("1.0"),
                "price__max": Decimal("2.0"),
                "price__avg": Decimal("1.50"),
            },
        )
        self.assertEqual(
            self.product.price_stats(exclude_discounted=True),
            {
                "price__count": 1,
                "price__min": Decimal("2.0"),
                "price__max": Decimal("2.0"),
                "price__avg": Decimal("2.00"),
            },
        )
