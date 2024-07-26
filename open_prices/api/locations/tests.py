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
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])


class LocationListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        LocationFactory(
            osm_id=652825274, osm_type="NODE", osm_name="Monoprix", price_count=15
        )
        LocationFactory(
            osm_id=6509705997, osm_type="NODE", osm_name="Carrefour", price_count=0
        )
        LocationFactory(
            osm_id=872934393, osm_type="WAY", osm_name="Auchan", price_count=50
        )

    def test_location_list_order_by(self):
        url = reverse("api:locations-list") + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["results"][0]["price_count"], 50)

    def test_location_list_filter_by_osm_name(self):
        url = reverse("api:locations-list") + "?osm_name__like=monop"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["osm_name"], "Monoprix")

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
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["price_count"], 15)


class LocationDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = LocationFactory(
            osm_id=652825274, osm_type="NODE", osm_name="Monoprix", price_count=15
        )

    def test_location_detail(self):
        # existing location
        url = reverse("api:locations-detail", args=[self.location.id])
        response = self.client.get(url)
        self.assertEqual(response.data["id"], self.location.id)
        # 404
        url = reverse("api:locations-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_location_detail_by_osm(self):
        # existing location
        url = reverse(
            "api:locations-get-by-osm",
            args=[self.location.osm_type, self.location.osm_id],
        )
        response = self.client.get(url)
        self.assertEqual(response.data["id"], self.location.id)
        # 404
        url = reverse("api:locations-get-by-osm", args=["NODE", 999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class LocationCreateApiTest(TestCase):
    def test_location_create(self):
        data = {
            "osm_id": 652825274,
            "osm_type": "NODE",
            "osm_name": "Monoprix",
            "price_count": 15,
        }
        url = reverse("api:locations-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["osm_id"], 652825274)
        self.assertEqual(response.data["osm_type"], "NODE")
        self.assertEqual(response.data["osm_name"], None)  # ignored
        self.assertEqual(response.data["price_count"], 0)  # ignored
