from django.test import TestCase

from open_prices.moderation.rules import cleanup_products_with_long_barcodes
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product


class ModerationRulesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product_ok = ProductFactory(code="0123456789100")  # 13 characters
        PriceFactory(product_code=cls.product_ok.code, source="mobile")
        PriceFactory(
            product_code=cls.product_ok.code,
            source="web - /experiments/price-validation-assistant",
        )
        cls.product_not_ok = ProductFactory(code="01234567891000")  # 14 characters
        PriceFactory(
            product_code=cls.product_not_ok.code,
            source="web - /experiments/price-validation-assistant",
        )

    def test_cleanup_products_with_long_barcodes(self):
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Price.objects.count(), 2 + 1)
        cleanup_products_with_long_barcodes()
        self.assertEqual(Product.objects.count(), 1)  # 1 product deleted
        self.assertEqual(Price.objects.count(), 2)  # 1 price deleted
