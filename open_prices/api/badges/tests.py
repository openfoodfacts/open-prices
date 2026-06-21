from django.test import TestCase
from django.urls import reverse

from open_prices.badges.factories import BadgeFactory


class BadgeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:badges-list")
        cls.badge_1 = BadgeFactory()
        cls.badge_2 = BadgeFactory()

    def test_badge_list(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(len(response.data["items"]), 2)


class BadgeListPaginationApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:badges-list")
        BadgeFactory()
        BadgeFactory()
        BadgeFactory()

    def test_badge_list_size(self):
        # default
        response = self.client.get(self.url)
        for PAGINATION_KEY in ["items", "page", "pages", "size", "total"]:
            with self.subTest(PAGINATION_KEY=PAGINATION_KEY):
                self.assertIn(PAGINATION_KEY, response.data)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(len(response.data["items"]), 3)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1)
        self.assertEqual(response.data["size"], 10)  # default


class BadgeListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:badges-list")
        cls.badge_1 = BadgeFactory()
        cls.badge_2 = BadgeFactory()

    def test_badge_list_default_order_by_id(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["items"]), 2)
        self.assertEqual(response.data["items"][0]["id"], self.badge_1.id)

    def test_badge_list_order_by(self):
        url = self.url + "?order_by=-id"
        response = self.client.get(url)
        self.assertEqual(len(response.data["items"]), 2)
        self.assertEqual(response.data["items"][0]["id"], self.badge_2.id)
