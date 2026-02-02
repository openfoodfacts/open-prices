from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.common.authentication import (
    get_token_from_cookie,
    get_token_from_header,
    has_token_from_cookie_or_header,
)
from open_prices.common.utils import (
    is_float,
    match_decimal_with_float,
    truncate_decimal,
    url_add_missing_https,
    url_keep_only_domain,
)
from open_prices.users.factories import SessionFactory

PRICE_8001505005707 = {
    "product_code": "8001505005707",
    "price": 15,
    "currency": "EUR",
    "date": "2024-01-01",
}


class AuthenticationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        cls.user_session = SessionFactory()

    def test_get_token_from_cookie(self):
        # wrong format & wrong token
        request = APIRequestFactory().get(self.url)
        request.COOKIES["Test"] = "Test"
        self.assertEqual(get_token_from_cookie(request), None)
        # wrong format & valid token
        request = APIRequestFactory().get(self.url)
        request.COOKIES["Test"] = self.user_session.token
        self.assertEqual(get_token_from_cookie(request), None)
        # valid format & wrong token
        request = APIRequestFactory().get(self.url)
        request.COOKIES[settings.SESSION_COOKIE_NAME] = "Test"
        self.assertEqual(get_token_from_cookie(request), "Test")
        # valid format & valid token
        request = APIRequestFactory().get(self.url)
        request.COOKIES[settings.SESSION_COOKIE_NAME] = self.user_session.token
        self.assertEqual(get_token_from_cookie(request), self.user_session.token)

    def test_get_token_from_header(self):
        # wrong format & wrong token
        request = APIRequestFactory().get(
            self.url,
            headers={"Authorization": "Test"},
        )
        self.assertEqual(get_token_from_header(request), None)
        # wrong format & valid token
        request = APIRequestFactory().get(
            self.url,
            headers={"Authorization": f"{self.user_session.token}"},  # "Bearer" missing
        )
        self.assertEqual(get_token_from_header(request), None)
        # valid format & wrong token
        request = APIRequestFactory().get(
            self.url,
            headers={"Authorization": "Bearer Test"},
        )
        self.assertEqual(get_token_from_header(request), "Test")
        # valid format & valid token
        request = APIRequestFactory().get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(get_token_from_header(request), self.user_session.token)
        # token is case-insensitive
        request = APIRequestFactory().get(
            self.url,
            headers={"Authorization": f"beAreR {self.user_session.token}"},
        )
        self.assertEqual(get_token_from_header(request), self.user_session.token)

    def test_has_token_from_cookie_or_header(self):
        # no token
        request = APIRequestFactory().get(self.url)
        self.assertFalse(has_token_from_cookie_or_header(request))
        # token in cookie
        request = APIRequestFactory().get(self.url)
        request.COOKIES[settings.SESSION_COOKIE_NAME] = "Test"
        self.assertTrue(has_token_from_cookie_or_header(request))
        # token in header
        request = APIRequestFactory().get(
            self.url, headers={"Authorization": "Bearer Test"}
        )
        self.assertTrue(has_token_from_cookie_or_header(request))


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

    def test_barcode_fix_short_codes_from_usa(self):
        for BARCODE_TUPLE in [
            ("9948252990", "0099482529901"),  # 10 digits (proof_id 49190)
            ("71627004002", "0716270040027"),  # 11 digits (proof_id 48443)
            ("471058718081", "4710587180816"),  # 12 digits (proof_id 48849)
            ("2006050050833", "2006050050833"),  # 13 digits valid
            ("S123456789", "S123456789"),  # non-numeric barcode should return as-is
        ]:
            with self.subTest(BARCODE_TUPLE=BARCODE_TUPLE):
                self.assertEqual(
                    common_openfoodfacts.barcode_fix_short_codes_from_usa(
                        BARCODE_TUPLE[0]
                    ),
                    BARCODE_TUPLE[1],
                )

    def test_get_smoothie_app_version(self):
        for source, expected_result in [
            (None, (None, None)),
            ("", (None, None)),
            ("Open Prices Web App - /proofs/add/single", (None, None)),
            ("API", (None, None)),
            (
                "Smoothie - OpenFoodFacts (4.20.0+1478) (android+U1TLS34.115-16-1-7-4)",
                (4, 20),
            ),
            ("Smoothie - OpenFoodFacts (4.20.1+1481) (android+2025070800)", (4, 20)),
            (
                "Smoothie - OpenFoodFacts (4.21.0+1500) (ios+Version 18.5 (Build 22F76))",
                (4, 21),
            ),
        ]:
            result = common_openfoodfacts.get_smoothie_app_version(source)
            self.assertEqual(result, expected_result)

    def test_is_smoothie_app_version_4_20(self):
        for source, expected_result in [
            (None, False),
            ("", False),
            ("Open Prices Web App - /proofs/add/single", False),
            ("API", False),
            (
                "Smoothie - OpenFoodFacts (4.20.0+1478) (android+U1TLS34.115-16-1-7-4)",
                True,
            ),
            ("Smoothie - OpenFoodFacts (4.20.1+1481) (android+2025070800)", True),
            (
                "Smoothie - OpenFoodFacts (4.21.0+1500) (ios+Version 18.5 (Build 22F76))",
                False,
            ),
        ]:
            result = common_openfoodfacts.is_smoothie_app_version_4_20(source)
            self.assertEqual(result, expected_result)

    def test_is_smoothie_app_version_leq_4_20(self):
        for source, expected_result in [
            (None, False),
            ("", False),
            ("Open Prices Web App - /proofs/add/single", False),
            ("API", False),
            (
                "Smoothie - OpenFoodFacts (4.19.9+1450) (ios+Version 18.5 (Build 22F76))",
                True,
            ),
            (
                "Smoothie - OpenFoodFacts (4.20.0+1478) (android+U1TLS34.115-16-1-7-4)",
                True,
            ),
            ("Smoothie - OpenFoodFacts (4.20.1+1481) (android+2025070800)", True),
            (
                "Smoothie - OpenFoodFacts (4.21.0+1500) (ios+Version 18.5 (Build 22F76))",
                False,
            ),
        ]:
            result = common_openfoodfacts.is_smoothie_app_version_leq_4_20(source)
            self.assertEqual(result, expected_result)


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
