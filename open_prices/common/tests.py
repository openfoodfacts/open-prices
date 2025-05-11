from decimal import Decimal

from django.test import TestCase

from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.common.utils import (
    is_float,
    match_decimal_with_float,
    truncate_decimal,
    url_add_missing_https,
    url_keep_only_domain,
)


class OpenFoodFactsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_barcode_is_valid(self):
        for BARCODE_OK in ["8001505005707"]:
            self.assertTrue(common_openfoodfacts.barcode_is_valid(BARCODE_OK))
        for BARCODE_NOT_OK in [
            "",
            " ",
            "a",
            "1234",
            "377247/3560071227302/480",
            "632461L236",
        ]:
            self.assertFalse(common_openfoodfacts.barcode_is_valid(BARCODE_NOT_OK))


class UtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_is_float(self):
        for PRICE_OK in [0, 1.5, 10, "0", "1.5", "10.00"]:
            self.assertTrue(is_float(PRICE_OK))
        for PRICE_NOT_OK in ["", " ", "a", "1,5", "1.5.0"]:
            self.assertFalse(is_float(PRICE_NOT_OK))

    def test_truncate_decimal(self):
        self.assertEqual(truncate_decimal("0.1234567"), "0.1234567")
        self.assertEqual(truncate_decimal("0.123456789"), "0.1234567")
        self.assertEqual(
            truncate_decimal("0.123456789", max_decimal_places=9), "0.123456789"
        )

    def test_match_decimal_with_float(self):
        self.assertTrue(match_decimal_with_float(Decimal("1"), 1))
        self.assertTrue(match_decimal_with_float(Decimal("1"), 1.0))
        self.assertTrue(match_decimal_with_float(Decimal("1.0"), 1))
        self.assertTrue(match_decimal_with_float(Decimal("1.0"), 1.0))
        self.assertTrue(match_decimal_with_float(Decimal("1.0"), 1.00))

    def url_add_missing_https(self):
        self.assertEqual(
            url_add_missing_https("http://abc.hostname.com/somethings/anything/"),
            "http://abc.hostname.com/somethings/anything/",
        )
        self.assertEqual(
            url_add_missing_https("abc.hostname.com/somethings/anything/"),
            "https://abc.hostname.com/somethings/anything/",
        )

    def test_url_keep_only_domain(self):
        self.assertEqual(
            url_keep_only_domain("http://abc.hostname.com/somethings/anything/"),
            "http://abc.hostname.com",
        )
        self.assertEqual(
            url_keep_only_domain("https://abc.hostname.com/somethings/anything/"),
            "https://abc.hostname.com",
        )
        self.assertEqual(
            url_keep_only_domain("abc.hostname.com/somethings/anything/"),
            "https://abc.hostname.com",
        )
        self.assertEqual(
            url_keep_only_domain("abc.hostname.com/"),
            "https://abc.hostname.com",
        )
        self.assertEqual(
            url_keep_only_domain("abc.hostname.com"),
            "https://abc.hostname.com",
        )
