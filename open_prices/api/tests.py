import base64

from django.test import TestCase
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
