from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory


class PriceModelSaveTest(TestCase):
    def test_price_product_validation(self):
        for PRODUCT_CODE_OK in ["8001505005707", 5]:
            PriceFactory(product_code=PRODUCT_CODE_OK)
        for PRODUCT_CODE_NOT_OK in ["...", 5.0, "8001505005707?", True, "None"]:
            self.assertRaises(
                ValidationError, PriceFactory, product_code=PRODUCT_CODE_NOT_OK
            )

    def test_price_without_product_validation(self):
        # product_code set
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            category_tag="en:tomatoes",
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            labels_tags=["en:organic"],
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            origins_tags=["en:france"],
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code="8001505005707",
            price_per=price_constants.PRICE_PER_UNIT,
        )
        # product_code not set
        PriceFactory(product_code=None, category_tag="en:tomatoes")
        self.assertRaises(
            ValidationError, PriceFactory, product_code=None, category_tag="test"
        )
        PriceFactory(
            product_code=None, category_tag="en:tomatoes", labels_tags=["en:organic"]
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic", "test"],
        )
        PriceFactory(
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags=["en:france"],
        )
        self.assertRaises(
            ValidationError,
            PriceFactory,
            product_code=None,
            category_tag="en:tomatoes",
            labels_tags=["en:organic"],
            origins_tags=["en:france", "test"],
        )
        # both product_code & category_tag not set
        self.assertRaises(
            ValidationError, PriceFactory, product_code="", category_tag=""
        )

    def test_price_price_validation(self):
        for PRICE_OK in [5, 0, None]:
            PriceFactory(price=PRICE_OK)
        for PRICE_NOT_OK in [-5, "test"]:  # True
            self.assertRaises(ValidationError, PriceFactory, price=PRICE_NOT_OK)

    def test_price_discount_validation(self):
        # price set, price_without_discount null
        PriceFactory(price=3, price_is_discounted=False, price_without_discount=None)
        PriceFactory(price=3, price_is_discounted=True, price_without_discount=None)
        # price null, price_without_discount set
        for PRICE_WITHOUT_DISCOUNT_OK in [5, 0, None]:
            PriceFactory(
                price=None,
                price_is_discounted=True,
                price_without_discount=PRICE_WITHOUT_DISCOUNT_OK,
            )
        for PRICE_WITHOUT_DISCOUNT_NOT_OK in [-5, "test"]:
            self.assertRaises(
                ValidationError,
                PriceFactory,
                price=None,
                price_is_discounted=True,
                price_without_discount=PRICE_WITHOUT_DISCOUNT_NOT_OK,
            )
        # both price & price_without_discount set
        PriceFactory(price=3, price_is_discounted=True, price_without_discount=5)
        self.assertRaises(
            ValidationError,
            PriceFactory,
            price=10,
            price_is_discounted=True,
            price_without_discount=5,
        )
