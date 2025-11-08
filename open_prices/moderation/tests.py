from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from open_prices.moderation import constants as moderation_constants
from open_prices.moderation.models import Flag
from open_prices.moderation.rules import (
    cleanup_products_with_invalid_barcodes,
    cleanup_products_with_long_barcodes,
)
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products import constants as product_constants
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof


class FlagModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        barcode = "8001505005707"
        cls.product = ProductFactory(code=barcode, source=product_constants.SOURCE_OFF)
        cls.proof = ProofFactory()
        cls.price = PriceFactory(
            product_code=cls.product.code, proof_id=cls.proof.id, source="mobile"
        )

    def test_create_flag_on_price(self):
        flag = self.price.flags.create(
            reason=moderation_constants.REASON_OTHER,
            comment="This price seems incorrect",
            owner="tester",
            source="unit-test",
        )

        self.assertEqual(Flag.objects.count(), 1)
        self.assertEqual(flag.content_type, ContentType.objects.get_for_model(Price))
        self.assertEqual(flag.content_object, self.price)
        self.assertEqual(flag.reason, moderation_constants.REASON_OTHER)
        self.assertEqual(flag.comment, "This price seems incorrect")
        self.assertEqual(flag.status, moderation_constants.STATUS_OPEN)  # default
        self.assertEqual(flag.owner, "tester")
        self.assertEqual(flag.source, "unit-test")
        self.assertEqual(self.price.flags.count(), 1)

    def test_create_flag_on_proof(self):
        flag = self.proof.flags.create(
            reason=moderation_constants.REASON_OTHER,
            comment="This proof seems incorrect",
            owner="tester",
            source="unit-test",
        )

        self.assertEqual(Flag.objects.count(), 1)
        self.assertEqual(flag.content_type, ContentType.objects.get_for_model(Proof))
        self.assertEqual(flag.content_object, self.proof)
        self.assertEqual(flag.reason, moderation_constants.REASON_OTHER)
        self.assertEqual(flag.comment, "This proof seems incorrect")
        self.assertEqual(flag.status, moderation_constants.STATUS_OPEN)  # default
        self.assertEqual(flag.owner, "tester")
        self.assertEqual(flag.source, "unit-test")
        self.assertEqual(self.proof.flags.count(), 1)


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
