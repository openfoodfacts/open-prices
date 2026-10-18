import base64

from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from factory.django import mute_signals

from open_prices.prices.factories import PriceFactory
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


class PaginationTest(TestCase):
    """
    There are already *PaginationApiTest in the different API test files.
    Here we add more tests for our custom pagination class.
    We'll run these tests on the Price list endpoint.
    """

    @classmethod
    def setUpTestData(cls):
        with mute_signals(post_save):
            PriceFactory.create_batch(1000)
        cls.url = reverse("api:prices-list")

    def test_pagination_size(self):
        # default
        response = self.client.get(self.url)
        for pagination_key in ["items", "page", "pages", "size", "total"]:
            with self.subTest(pagination_key=pagination_key):
                self.assertIn(pagination_key, response.data)
        self.assertEqual(response.data["total"], 1000)
        self.assertEqual(len(response.data["items"]), 10)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 100)
        self.assertEqual(response.data["size"], 10)  # default
        # size=150
        url = self.url + "?size=150"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1000)
        self.assertEqual(len(response.data["items"]), 100)  # max to 100
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 10)
        self.assertEqual(response.data["size"], 100)  # max to 100
        # size=1
        url = self.url + "?size=1"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1000)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1000)
        self.assertEqual(response.data["size"], 1)

    def test_pagination_page_number(self):
        # size=1 & page=1
        url = self.url + "?size=1&page=1"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1000)
        # size=1 & page=500
        url = self.url + "?size=1&page=500"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 500)
        self.assertEqual(response.data["pages"], 1000)
        # size=1 & page=501
        url = self.url + "?size=1&page=501"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)  # max page is 500
        self.assertIn("Maximum page reached", response.json()["detail"])
        # size=10 & page=1 (default)
        response = self.client.get(self.url)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 100)
        # size=10 & page=1
        url = self.url + "?page=1"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 100)
        # size=10 & page=2
        url = self.url + "?page=2"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["pages"], 100)
        # size=10 & page=100
        url = self.url + "?page=100"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 100)
        self.assertEqual(response.data["pages"], 100)
        # size=10 & page=101
        url = self.url + "?page=101"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # last page is 100
        # size=100 & page=1
        url = self.url + "?size=100&page=1"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 10)
        # size=100 & page=10
        url = self.url + "?size=100&page=10"
        response = self.client.get(url)
        self.assertEqual(response.data["page"], 10)
        self.assertEqual(response.data["pages"], 10)
        # size=100 & page=11
        url = self.url + "?size=100&page=11"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # last page is 10
        # page=last
        url = self.url + "?page=last"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)  # last page string is disabled
        self.assertIn("Invalid page", response.json()["detail"])
        # page=0
        url = self.url + "?page=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)  # invalid page number
        self.assertIn("Invalid page", response.json()["detail"])
