import base64

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from open_prices.users.factories import SessionFactory


class StatusTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:status")
        cls.user_session = SessionFactory()

    def test_get_status(self):
        for HEADERS_OK in [
            {},
            {"Authorization": f"Bearer {self.user_session.token}"},
            {"Authorization": f"Bearer {self.user_session.token}X"},
            {"Authorization": f"Basic {base64.b64encode(b'username:password')}"},
        ]:
            with self.subTest(HEADERS_OK=HEADERS_OK):
                response = self.client.get(self.url, headers=HEADERS_OK)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "running"})


class RateLimitConfigTests(SimpleTestCase):
    def test_anon_throttle_class_configured(self):
        from django.conf import settings

        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])
        self.assertIn(
            "rest_framework.throttling.AnonRateThrottle",
            throttle_classes,
        )

    def test_user_throttle_class_configured(self):
        from django.conf import settings

        throttle_classes = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])
        self.assertIn(
            "rest_framework.throttling.UserRateThrottle",
            throttle_classes,
        )

    def test_anon_throttle_rate_set(self):
        from django.conf import settings

        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("anon", throttle_rates)

    def test_user_throttle_rate_set(self):
        from django.conf import settings

        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("user", throttle_rates)

    def test_pagination_max_page_size_enforced(self):
        from open_prices.api.pagination import CustomPagination

        self.assertIsNotNone(CustomPagination.max_page_size)
        self.assertLessEqual(CustomPagination.max_page_size, 100)
