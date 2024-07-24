from django.test import TestCase
from django.urls import reverse

from open_prices.prices.factories import PriceFactory


class PriceListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PriceFactory(price=15)
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list(self):
        url = reverse("api:prices-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("id" in response.data["results"][0])


class PriceListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PriceFactory(price=15)
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list_order_by(self):
        url = reverse("api:prices-list") + "?order_by=-price"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["price"], 50)

    def test_price_list_filter_by_price(self):
        # exact price
        url = reverse("api:prices-list") + "?price=15"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price"], 15)
        # lte / gte
        url = reverse("api:prices-list") + "?price__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price"], 50)
        url = reverse("api:prices-list") + "?price__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price"], 15)
