from django.test import TestCase
from django.urls import reverse

from open_prices.users.factories import UserFactory
from open_prices.users.models import User


class UserListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:users-list")
        UserFactory(user_id="dan", price_count=15)
        UserFactory(user_id="alice", price_count=0)
        UserFactory(user_id="bob", price_count=50)

    def test_user_list(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 2)  # only users with prices
        self.assertEqual(len(response.data["items"]), 2)
        self.assertFalse("id" in response.data["items"][0])
        self.assertEqual(response.data["items"][0]["user_id"], "bob")  # default order
        for field_name in User.SERIALIZED_FIELDS:
            self.assertTrue(field_name in response.data["items"][0])


class UserListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:users-list")
        UserFactory(price_count=15)
        UserFactory(price_count=0)
        UserFactory(price_count=50, location_count=5, product_count=25)

    def test_user_list_order_by_price_count(self):
        url = self.url + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)  # only users with prices
        self.assertEqual(response.data["items"][0]["price_count"], 50)

    def test_user_list_order_by_location_count(self):
        url = self.url + "?order_by=-location_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)  # only users with prices
        self.assertEqual(response.data["items"][0]["location_count"], 5)

    def test_user_list_order_by_product_count(self):
        url = self.url + "?order_by=-product_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)  # only users with prices
        self.assertEqual(response.data["items"][0]["product_count"], 25)


class UserListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:users-list")
        UserFactory(price_count=15)
        UserFactory(price_count=0)
        UserFactory(price_count=50)

    def test_user_list_filter_by_price_count(self):
        # exact price_count
        url = self.url + "?price_count=15"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price_count"], 15)
        # lte / gte
        url = self.url + "?price_count__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price_count"], 50)
        url = self.url + "?price_count__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price_count"], 15)
