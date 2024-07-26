from django.test import TestCase
from django.urls import reverse

from open_prices.prices.factories import PriceFactory
from open_prices.users.factories import SessionFactory


class PriceListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PriceFactory(price=15)
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list(self):
        url = reverse("api:prices-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])


class PriceListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PriceFactory(
            product_code="8001505005707", price=15, currency="EUR", date="2024-01-01"
        )
        PriceFactory(price=0, currency="EUR", date="2023-08-30")
        PriceFactory(price=50, currency="USD", date="2024-06-30")

    def test_price_list_order_by(self):
        url = reverse("api:prices-list") + "?order_by=-price"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["results"][0]["price"], "50.00")

    def test_price_list_filter_by_product_code(self):
        url = reverse("api:prices-list") + "?product_code=8001505005707"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)

    def test_price_list_filter_by_price(self):
        # exact price
        url = reverse("api:prices-list") + "?price=15"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price"], "15.00")
        # lte / gte
        url = reverse("api:prices-list") + "?price__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price"], "50.00")
        url = reverse("api:prices-list") + "?price__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["price"], "15.00")

    def test_price_list_filter_by_currency(self):
        url = reverse("api:prices-list") + "?currency=EUR"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)

    def test_price_list_filter_by_date(self):
        # exact date
        url = reverse("api:prices-list") + "?date=2024-01-01"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        # lte / gte
        url = reverse("api:prices-list") + "?date__gte=2024-01-01"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)


class PriceCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()

    def test_price_create(self):
        data = {
            "product_code": "8001505005707",
            "price": 15,
            "currency": "EUR",
            "date": "2024-01-01",
            "source": "test",
        }
        url = reverse("api:prices-list")
        # anonymous
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.post(
            url,
            data,
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        # authenticated
        response = self.client.post(
            url,
            data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["product_code"], "8001505005707")
        self.assertEqual(response.data["price"], "15.00")
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["date"], "2024-01-01")
        self.assertEqual(response.data["source"], None)  # ignored
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
