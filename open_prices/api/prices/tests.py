from django.db.models import signals
from django.test import TestCase
from django.urls import reverse

from open_prices.locations.models import (
    Location,
    location_post_create_fetch_data_from_openstreetmap,
)
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.models import (
    Product,
    product_post_create_fetch_data_from_openfoodfacts,
)
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import SessionFactory


class PriceListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        PriceFactory(price=15)
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])


class PriceListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PriceFactory(
            product_code="8001505005707",
            price=15,
            currency="EUR",
            date="2024-01-01",
            owner="user_1",
        )
        PriceFactory(price=0, currency="EUR", date="2023-08-30", owner="user_1")
        PriceFactory(price=50, currency="USD", date="2024-06-30", owner="user_2")

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
        # month
        url = reverse("api:prices-list") + "?date__month=1"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        # year
        url = reverse("api:prices-list") + "?date__year=2024"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)

    def test_price_list_filter_by_owner(self):
        url = reverse("api:prices-list") + "?owner=user_1"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)


class PriceDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.price = PriceFactory(
            product_code="8001505005707",
            price=15,
            currency="EUR",
            date="2024-01-01",
            owner=cls.user_session_1.user.user_id,
        )
        cls.url = reverse("api:prices-detail", args=[cls.price.id])

    def test_price_detail_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class PriceCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        signals.post_save.disconnect(
            product_post_create_fetch_data_from_openfoodfacts, sender=Product
        )
        signals.post_save.disconnect(
            location_post_create_fetch_data_from_openstreetmap, sender=Location
        )
        cls.url = reverse("api:prices-list")
        cls.user_session = SessionFactory()
        cls.user_proof = ProofFactory(owner=cls.user_session.user.user_id)
        cls.proof_2 = ProofFactory()
        cls.data = {
            "product_code": "8001505005707",
            "price": 15,
            "currency": "EUR",
            "location_osm_id": 652825274,
            "location_osm_type": "NODE",
            "date": "2024-01-01",
            "proof_id": cls.user_proof.id,
            "source": "test",
        }

    def test_price_create(self):
        # anonymous
        response = self.client.post(
            self.url, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        # proof_id field missing
        data = self.data.copy()
        del data["proof_id"]
        response = self.client.post(
            self.url,
            data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # empty proof
        response = self.client.post(
            self.url,
            {**self.data, "proof_id": None},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # unknown proof
        response = self.client.post(
            self.url,
            {**self.data, "proof_id": 999},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # not proof owner
        response = self.client.post(
            self.url,
            {**self.data, "proof_id": self.proof_2.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # authenticated
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["product_code"], "8001505005707")
        self.assertEqual(response.data["price"], "15.00")
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["date"], "2024-01-01")
        self.assertTrue("source" not in response.data)
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
        # with proof, product & location
        self.assertEqual(response.data["proof"]["id"], self.user_proof.id)
        self.assertEqual(response.data["product"]["code"], "8001505005707")
        self.assertEqual(response.data["location"]["osm_id"], 652825274)
        p = Price.objects.last()
        self.assertIsNone(p.source)  # ignored

    def test_price_create_with_app_name(self):
        for app_name in ["", "test app"]:
            response = self.client.post(
                self.url + f"?app_name={app_name}",
                self.data,
                headers={"Authorization": f"Bearer {self.user_session.token}"},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 201)
            self.assertTrue("source" not in response.data)
            p = Price.objects.last()
            self.assertEqual(p.source, app_name)


class PriceUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.price = PriceFactory(
            product_code="8001505005707",
            price=15,
            currency="EUR",
            date="2024-01-01",
            owner=cls.user_session_1.user.user_id,
        )
        cls.url = reverse("api:prices-detail", args=[cls.price.id])
        cls.data = {"currency": "USD", "product_code": "123"}

    def test_price_update(self):
        # anonymous
        response = self.client.patch(
            self.url, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}X"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        # not price owner
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_2.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)  # 403 ?
        # authenticated
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["currency"], "USD")
        self.assertEqual(
            Price.objects.get(id=self.price.id).product_code, "8001505005707"
        )  # ignored


class PriceDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.price = PriceFactory(
            product_code="8001505005707",
            price=15,
            currency="EUR",
            date="2024-01-01",
            owner=cls.user_session_1.user.user_id,
        )
        cls.url = reverse("api:prices-detail", args=[cls.price.id])

    def test_price_delete(self):
        # anonymous
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}X"}
        )
        self.assertEqual(response.status_code, 403)
        # not price owner
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_2.token}"}
        )
        self.assertEqual(response.status_code, 404)  # 403 ?
        # authenticated
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertEqual(
            Price.objects.filter(owner=self.user_session_1.user.user_id).count(), 0
        )
