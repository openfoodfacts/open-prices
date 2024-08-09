from django.test import TestCase

from open_prices.common.utils import is_float


class UtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_is_float(self):
        for PRICE_OK in [0, 1.5, 10, "0", "1.5", "10.00"]:
            self.assertTrue(is_float(PRICE_OK))
        for PRICE_NOT_OK in ["", " ", "a", "1,5", "1.5.0"]:
            self.assertFalse(is_float(PRICE_NOT_OK))
