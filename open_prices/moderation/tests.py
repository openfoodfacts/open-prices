from django.test import TestCase

from open_prices.moderation.rules import (
    cleanup_products_with_invalid_barcodes,
    cleanup_products_with_long_barcodes,
)
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products import constants as product_constants
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product


class ModerationRulesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        barcode_ok = "8001505005707"
        cls.product_ok = ProductFactory(
            code=barcode_ok, source=product_constants.SOURCE_OFF
        )
        PriceFactory(product_code=cls.product_ok.code, source="mobile")
        PriceFactory(
            product_code=cls.product_ok.code,
            source="web - /experiments/price-validation-assistant",
        )
        barcode_invalid = "0123456789100"
        cls.product_with_barcode_invalid = ProductFactory(
            code=barcode_invalid, source=None
        )
        PriceFactory(
            product_code=cls.product_with_barcode_invalid.code, source="mobile"
        )
        PriceFactory(
            product_code=cls.product_with_barcode_invalid.code,
            source="web - /experiments/price-validation-assistant",
        )
        barcode_long_and_invalid = "61234567891000"
        cls.product_with_barcode_long_and_invalid = ProductFactory(
            code=barcode_long_and_invalid, source=None
        )
        PriceFactory(
            product_code=cls.product_with_barcode_long_and_invalid.code,
            source="web - /experiments/price-validation-assistant",
        )

    def test_cleanup_products_with_long_barcodes(self):
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(Price.objects.count(), 5)
        cleanup_products_with_long_barcodes()
        self.assertEqual(Product.objects.count(), 2)  # 1 product deleted
        self.assertEqual(Price.objects.count(), 4)  # 1 price deleted

    def test_cleanup_products_with_invalid_barcodes(self):
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(Price.objects.count(), 5)
        cleanup_products_with_invalid_barcodes()
        self.assertEqual(Product.objects.count(), 2)  # 1 product deleted
        self.assertEqual(Price.objects.count(), 3)  # 2 prices deleted
