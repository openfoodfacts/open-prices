from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.products.factories import ProductFactory
from open_prices.users.factories import SessionFactory

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_address_country": "France",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
    "price_count": 15,
}
LOCATION_OSM_NODE_6509705997 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 6509705997,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Carrefour",
    "price_count": 0,
}
LOCATION_OSM_WAY_872934393 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 872934393,
    "osm_type": "WAY",
    "osm_name": "Auchan",
    "price_count": 50,
}
LOCATION_ONLINE_DECATHLON = {
    "type": location_constants.TYPE_ONLINE,
    "website_url": "https://www.decathlon.fr",
    "price_count": 15,
}
PRODUCT_8001505005707 = {
    "code": "8001505005707",
    "product_name": "Nocciolata",
    "categories_tags": ["en:breakfasts", "en:spreads"],
    "labels_tags": ["en:no-gluten", "en:organic"],
    "brands_tags": ["rigoni-di-asiago"],
    "price_count": 15,
    "source": "off",
}

PRODUCT_8850187002197 = {
    "code": "8850187002197",
    "product_name": "Riz 20 kg",
    "categories_tags": ["en:rices"],
    "labels_tags": [],
    "brands_tags": ["royal-umbrella"],
    "price_count": 10,
}


class LocationListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-list")
        LocationFactory(price_count=15)
        LocationFactory(price_count=0)
        LocationFactory(price_count=50)

    def test_location_list(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(len(response.data["items"]), 3)
        self.assertTrue("id" in response.data["items"][0])
        self.assertEqual(response.data["items"][0]["price_count"], 15)  # default order


class LocationListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-list")
        LocationFactory(price_count=15)
        LocationFactory(price_count=0)
        LocationFactory(price_count=50)

    def test_location_list_order_by(self):
        url = self.url + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["price_count"], 50)


class LocationListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-list")
        LocationFactory(**LOCATION_OSM_NODE_652825274)
        LocationFactory(**LOCATION_OSM_NODE_6509705997)
        LocationFactory(**LOCATION_OSM_WAY_872934393)
        LocationFactory(**LOCATION_ONLINE_DECATHLON)

    def test_location_list_filter_by_osm_name(self):
        url = self.url + "?osm_name__like=monop"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["osm_name"], "Monoprix")

    def test_location_list_filter_by_type(self):
        url = self.url + "?type=ONLINE"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["type"], location_constants.TYPE_ONLINE
        )

    def test_location_list_filter_by_price_count(self):
        # exact price_count
        url = self.url + "?price_count=15"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1 + 1)
        self.assertEqual(response.data["items"][0]["price_count"], 15)
        # lte / gte
        url = self.url + "?price_count__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price_count"], 50)
        url = self.url + "?price_count__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["price_count"], 15)


class LocationDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.url = reverse("api:locations-detail", args=[cls.location.id])

    def test_location_detail(self):
        # 404
        url = reverse("api:locations-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"], "No Location matches the given query."
        )
        # existing location
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.location.id)
        # self.assertEqual(response.data["osm_lat"], 45.1805534)

    def test_location_detail_by_osm(self):
        # 404
        url = reverse("api:locations-get-by-osm", args=["NODE", 999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"], "No Location matches the given query."
        )
        # existing location
        url = reverse(
            "api:locations-get-by-osm",
            args=[self.location.osm_type, self.location.osm_id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.location.id)


class LocationCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-list")

    def test_location_create_osm(self):
        response = self.client.post(
            self.url, LOCATION_OSM_NODE_652825274, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["osm_id"], 652825274)
        self.assertEqual(response.data["osm_type"], "NODE")
        self.assertEqual(
            response.data["osm_name"], None
        )  # ignored (and post_save signal disabled)
        self.assertEqual(response.data["price_count"], 0)  # ignored

    def test_location_create_online(self):
        response = self.client.post(
            self.url, LOCATION_ONLINE_DECATHLON, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["website_url"], "https://www.decathlon.fr")
        self.assertEqual(response.data["price_count"], 0)  # ignored

    def test_location_create_duplicate(self):
        LocationFactory(**LOCATION_OSM_NODE_652825274)
        LocationFactory(**LOCATION_ONLINE_DECATHLON)
        for location in [LOCATION_OSM_NODE_652825274, LOCATION_ONLINE_DECATHLON]:
            with self.subTest(location=location):
                data = {
                    **location,
                    "price_count": 0,
                }
                response = self.client.post(
                    self.url, data, content_type="application/json"
                )
                self.assertEqual(response.status_code, 200)  # instead of 201
                self.assertEqual(
                    response.data["osm_id"],
                    location["osm_id"] if "osm_id" in location else None,
                )
                self.assertEqual(
                    response.data["website_url"],
                    location["website_url"] if "website_url" in location else None,
                )
                self.assertEqual(
                    response.data["price_count"], location["price_count"]
                )  # unchanged
                self.assertEqual(response.data["detail"], "duplicate")

    def test_location_create_with_app_name(self):
        for index, (params, result) in enumerate(
            [
                ("?", "API"),
                ("?app_name=", ""),
                ("?app_name=test app&app_version=", "test app"),
                ("?app_name=mobile&app_version=1.0", "mobile (1.0)"),
                (
                    "?app_name=web&app_version=&app_page=/prices/add/multiple",
                    "web - /prices/add/multiple",
                ),
            ]
        ):
            with self.subTest(INPUT_OUPUT=(params, result)):
                data = {
                    **LOCATION_OSM_NODE_652825274,
                    "osm_id": LOCATION_OSM_NODE_652825274["osm_id"] + index,
                }
                # with empty app_name
                response = self.client.post(
                    self.url + params, data, content_type="application/json"
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data["source"], result)
                self.assertEqual(Location.objects.last().source, result)


class LocationUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.location = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.url = reverse("api:locations-detail", args=[cls.location.id])
        cls.data = {"osm_name": "Carrefour"}

    def test_location_update_not_allowed(self):
        # anonymous
        response = self.client.patch(
            self.url, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 405)
        # authenticated
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 405)


class LocationDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.location = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.url = reverse("api:locations-detail", args=[cls.location.id])

    def test_location_delete_not_allowed(self):
        # anonymous
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 405)
        # authenticated
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session.token}"}
        )
        self.assertEqual(response.status_code, 405)


class LocationOsmCountriesListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-list-osm-countries")
        cls.location_fr = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_address_country_code="FR",
            price_count=5,
        )
        cls.location_ch = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_address_country_code="CH",
            price_count=0,
        )

    def test_location_osm_countries(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))
        self.assertEqual(len(response.data), 238)
        country_fr = next(c for c in response.data if c["country_code_2"] == "FR")
        self.assertEqual(country_fr["location_count"], 1)
        self.assertEqual(country_fr["price_count"], 5)
        country_ch = next(c for c in response.data if c["country_code_2"] == "CH")
        self.assertEqual(country_ch["location_count"], 1)
        self.assertEqual(country_ch["price_count"], 0)
        country_us = next(c for c in response.data if c["country_code_2"] == "US")
        self.assertEqual(country_us["location_count"], 0)
        self.assertEqual(country_us["price_count"], 0)


class LocationOsmCountryCitiesListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-list-osm-country-cities", args=["FR"])
        cls.location_fr_paris = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_address_country_code="FR",
            osm_address_city="Paris",
            price_count=5,
        )
        cls.location_fr_grenoble = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_address_country_code="FR",
            osm_address_city="Grenoble",
            price_count=10,
        )
        cls.location_fr_grenoble = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_address_country_code="FR",
            osm_address_city="Grenoble",
            price_count=0,
        )
        cls.location_ch_geneva = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_address_country_code="CH",
            osm_address_city="Geneva",
            price_count=0,
        )

    def test_location_osm_country_cities(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["osm_name"], "Grenoble")  # ordered by name
        self.assertEqual(response.data[0]["country_code_2"], "FR")
        self.assertEqual(response.data[0]["location_count"], 2)
        self.assertEqual(response.data[0]["price_count"], 10)


class LocationCompareApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:locations-compare")
        cls.location_a = LocationFactory(
            type=location_constants.TYPE_OSM,
            price_count=5,
        )
        cls.location_b = LocationFactory(
            type=location_constants.TYPE_OSM,
            price_count=2,
        )
        cls.location_c = LocationFactory(
            type=location_constants.TYPE_OSM,
            price_count=0,
        )
        cls.product_8001505005707 = ProductFactory(**PRODUCT_8001505005707)
        cls.product_8850187002197 = ProductFactory(**PRODUCT_8850187002197)
        PriceFactory(
            location=cls.location_a,
            location_osm_id=cls.location_a.osm_id,
            location_osm_type=cls.location_a.osm_type,
            product_code=cls.product_8001505005707.code,
            price=1.5,
            date="2024-01-01",
        )
        PriceFactory(
            location=cls.location_a,
            location_osm_id=cls.location_a.osm_id,
            location_osm_type=cls.location_a.osm_type,
            product_code=cls.product_8850187002197.code,
            price=2.5,
            date="2024-01-01",
        )
        # location b has 2 prices (1 shared)
        PriceFactory(
            location=cls.location_b,
            location_osm_id=cls.location_b.osm_id,
            location_osm_type=cls.location_b.osm_type,
            product_code=cls.product_8001505005707.code,
            price=1.0,
            date="2025-01-01",
        )
        PriceFactory(
            location=cls.location_b,
            location_osm_id=cls.location_b.osm_id,
            location_osm_type=cls.location_b.osm_type,
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:apples",
            price=2,
            price_per=price_constants.PRICE_PER_KILOGRAM,
            date="2025-01-01",
        )

    def test_cannot_compare_with_bad_request(self):
        # missing parameter
        url = f"{self.url}?location_id_a={self.location_a.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

        # location parameter must be an integer
        url = f"{self.url}?location_id_a={self.location_a.id}&location_id_b=invalid"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

        # location unknown
        url = f"{self.url}?location_id_a={self.location_a.id}&location_id_b=999"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_compare_same_location(self):
        url = f"{self.url}?location_id_a={self.location_a.id}&location_id_b={self.location_a.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

    def test_compare_no_shared_products(self):
        url = f"{self.url}?location_id_a={self.location_a.id}&location_id_b={self.location_c.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["shared_products"], [])
        self.assertEqual(response.data["total_sum_location_a"], Decimal("0"))
        self.assertEqual(response.data["total_sum_location_b"], Decimal("0"))

    def test_compare_shared_products(self):
        url = f"{self.url}?location_id_a={self.location_a.id}&location_id_b={self.location_b.id}"

        # 3 queries: 2 for fetching both locations, 1 for fetching all prices
        with self.assertNumQueries(2 + 1):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["location_a"]["id"], self.location_a.id)
        self.assertEqual(response.data["location_b"]["id"], self.location_b.id)
        self.assertEqual(len(response.data["shared_products"]), 1)
        shared_product = response.data["shared_products"][0]
        self.assertEqual(
            shared_product["product_code"], self.product_8001505005707.code
        )
        self.assertEqual(
            shared_product["product_name"], self.product_8001505005707.product_name
        )
        self.assertEqual(shared_product["location_a"]["price"], Decimal("1.5"))
        self.assertEqual(shared_product["location_b"]["price"], Decimal("1.0"))
        self.assertEqual(response.data["total_sum_location_a"], Decimal("1.5"))
        self.assertEqual(response.data["total_sum_location_b"], Decimal("1.0"))

    def test_compare_shared_products_with_date_filter(self):
        url = f"{self.url}?location_id_a={self.location_a.id}&location_id_b={self.location_b.id}&date__gte=2024-12-31"

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["shared_products"]), 0)
        self.assertEqual(response.data["total_sum_location_a"], Decimal("0"))
        self.assertEqual(response.data["total_sum_location_b"], Decimal("0"))
