from django.test import TestCase
from django.urls import reverse

from open_prices.locations.factories import LocationFactory


class LocationListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        LocationFactory(price_count=15)
        LocationFactory(price_count=0)
        LocationFactory(price_count=50)

    def test_location_list(self):
        url = reverse("api:locations-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("id" in response.data["results"][0])


class LocationListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        LocationFactory(price_count=15)
        LocationFactory(price_count=0)
        LocationFactory(price_count=50)

    def test_location_list_order_by(self):
        url = reverse("api:locations-list") + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["price_count"], 50)

    def test_location_list_filter_by_price_count(self):
        # exact price_count
        url = reverse("api:locations-list") + "?price_count=15"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 15)
        # lte / gte
        url = reverse("api:locations-list") + "?price_count__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 50)
        url = reverse("api:locations-list") + "?price_count__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 15)
