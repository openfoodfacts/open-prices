from django.test import TestCase
from django.urls import reverse

from open_prices.users.factories import SessionFactory, UserFactory
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
        UserFactory(price_count=50, location_count=5, product_count=25, proof_count=10)

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

    def test_user_list_order_by_proof_count(self):
        url = self.url + "?order_by=-proof_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)  # only users with prices
        self.assertEqual(response.data["items"][0]["proof_count"], 10)


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


class UserDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.url = reverse("api:users-detail", args=[cls.user_session_1.user.user_id])

    def test_user_detail(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # anonymous, unknown user
        url = reverse("api:users-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # authenticated, unknown user
        response = self.client.get(
            url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 404)
        # authenticated, but not owner
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.user_session_2.token}"}
        )
        self.assertEqual(response.status_code, 200)
        # authenticated and owner
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_id"], self.user_session_1.user.user_id)
