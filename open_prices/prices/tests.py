from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.prices.factories import PriceFactory


class PriceModelSaveTest(TestCase):
    def test_price_price_validation(self):
        for PRICE_OK in [5, 0, None]:
            PriceFactory(price=PRICE_OK)
        for PRICE_NOT_OK in [-5, "test"]:
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
