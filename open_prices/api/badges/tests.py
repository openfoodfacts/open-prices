from django.test import TestCase
from django.urls import reverse

from open_prices.badges.factories import BadgeFactory
from open_prices.users.factories import SessionFactory


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


class BadgeCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:badges-list")

    def test_cannot_create_badge(self):
        response = self.client.post(self.url, data={"name": "New Badge"})
        self.assertEqual(response.status_code, 405)


class BadgeDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.badge = BadgeFactory()

    def test_badge_detail(self):
        # 404
        url = reverse("api:badges-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "No Badge matches the given query.")
        # existing badge
        url = reverse("api:badges-detail", args=[self.badge.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.badge.id)
        self.assertEqual(response.data["name"], self.badge.name)


class BadgeUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.badge = BadgeFactory()
        cls.url = reverse("api:badges-detail", args=[cls.badge.id])
        cls.data = {"name": "Updated Badge Name"}

    def test_cannot_update_badge(self):
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


class BadgeDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.badge = BadgeFactory()
        cls.url = reverse("api:badges-detail", args=[cls.badge.id])

    def test_cannot_delete_badge(self):
        # anonymous
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 405)
        # authenticated
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session.token}"}
        )
        self.assertEqual(response.status_code, 405)
