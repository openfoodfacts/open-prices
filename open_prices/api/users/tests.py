from django.test import TestCase
from django.urls import reverse

from open_prices.users.factories import UserFactory
from open_prices.users.models import User


class UserListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        UserFactory(price_count=15)
        UserFactory(price_count=0)
        UserFactory(price_count=50)

    def test_user_list(self):
        url = reverse("api:users-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertFalse("id" in response.data["results"][0])
        for field_name in User.SERIALIZED_FIELDS:
            self.assertTrue(field_name in response.data["results"][0])


class UserListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        UserFactory(price_count=15)
        UserFactory(price_count=0)
        UserFactory(price_count=50)

    def test_user_list_order_by(self):
        url = reverse("api:users-list") + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["price_count"], 50)

    def test_user_list_filter_by_price_count(self):
        # exact price_count
        url = reverse("api:users-list") + "?price_count=15"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 15)
        # lte / gte
        url = reverse("api:users-list") + "?price__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 50)
        url = reverse("api:users-list") + "?price__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 15)
