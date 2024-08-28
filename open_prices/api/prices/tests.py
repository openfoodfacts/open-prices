from django.db.models import signals
from django.test import TestCase
from django.urls import reverse

from open_prices.locations.models import (
    Location,
    location_post_create_fetch_data_from_openstreetmap,
)
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.models import (
    Product,
    product_post_create_fetch_data_from_openfoodfacts,
)
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import SessionFactory

PRICE_8001505005707 = {
    "product_code": "8001505005707",
    "price": 15,
    "currency": "EUR",
    "date": "2024-01-01",
}


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
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(len(response.data["items"]), 3)
        self.assertTrue("id" in response.data["items"][0])
        self.assertEqual(response.data["items"][0]["price"], 15.00)  # default order


class PriceListPaginationApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        PriceFactory(price=15)
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list_size(self):
        # default
        response = self.client.get(self.url)
        for PAGINATION_KEY in ["items", "page", "pages", "size", "total"]:
            with self.subTest(PAGINATION_KEY=PAGINATION_KEY):
                self.assertTrue(PAGINATION_KEY in response.data)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(len(response.data["items"]), 3)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1)
        self.assertEqual(response.data["size"], 100)
        self.assertEqual(response.data["items"][0]["price"], 15.00)  # default order
        # size=1
        url = self.url + "?size=1"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 3)
        self.assertEqual(response.data["size"], 1)
        self.assertEqual(response.data["items"][0]["price"], 15.00)  # default order


class PriceListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        PriceFactory(price=15)
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list_order_by(self):
        url = self.url + "?order_by=-price"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["price"], 50.00)


class PriceListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        cls.user_session = SessionFactory()
        cls.user_proof = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, owner=cls.user_session.user.user_id
        )
        cls.user_price = PriceFactory(
            **PRICE_8001505005707,
            proof_id=cls.user_proof.id,
            owner=cls.user_session.user.user_id,
        )
        PriceFactory(
            product_code=None,
            category_tag="en:croissants",
            price_per=price_constants.PRICE_PER_UNIT,
            price=1,
            currency="EUR",
            date="2023-08-30",
            owner=cls.user_session.user.user_id,
        )
        PriceFactory(
            price=50,
            price_without_discount=70,
            price_is_discounted=True,
            currency="USD",
            location_osm_id=None,
            location_osm_type=None,
            date="2024-06-30",
            owner="user_2",
        )

    def test_price_list_without_filter(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 3)

    def test_price_list_filter_by_product(self):
        # product_code
        url = self.url + "?product_code=8001505005707"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["product_code"], "8001505005707")
        # product_id__isnull
        url = self.url + "?product_id__isnull=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["category_tag"], "en:croissants")
        url = self.url + "?product_id__isnull=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        # category_tag
        url = self.url + "?category_tag=croissants"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 0)
        url = self.url + "?category_tag=en:croissants"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)

    def test_price_list_filter_by_price(self):
        # exact price
        url = self.url + "?price=15"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price"], 15.00)
        # lte / gte
        url = self.url + "?price__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price"], 50.00)
        url = self.url + "?price__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["items"][0]["price"], 15.00)
        # price_is_discounted
        url = self.url + "?price_is_discounted=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price"], 50.00)
        url = self.url + "?price_is_discounted=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)

    def test_price_list_filter_by_currency(self):
        url = self.url + "?currency=EUR"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)

    def test_price_list_filter_by_location(self):
        # location_osm_id
        url = self.url + f"?location_osm_id={self.user_price.location_osm_id}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # location_id
        url = self.url + f"?location_id={self.user_price.location_id}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # location_id__isnull
        url = self.url + "?location_id__isnull=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        url = self.url + "?location_id__isnull=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)

    def test_price_list_filter_by_proof(self):
        # proof_id
        url = self.url + f"?proof_id={self.user_price.proof_id}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # proof_id__isnull
        url = self.url + "?proof_id__isnull=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        url = self.url + "?proof_id__isnull=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)

    def test_price_list_filter_by_date(self):
        # exact date
        url = self.url + "?date=2024-01-01"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # lte / gte
        url = self.url + "?date__gte=2024-01-01"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        # month
        url = self.url + "?date__month=1"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # year
        url = self.url + "?date__year=2024"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)

    def test_price_list_filter_by_owner(self):
        url = self.url + f"?owner={self.user_session.user.user_id}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)

    def test_price_list_filter_by_created(self):
        url = self.url + "?created__gte=2024-01-01T00:00:00Z"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        url = self.url + "?created__lte=2024-01-01T00:00:00Z"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 0)


class PriceDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.price = PriceFactory(
            **PRICE_8001505005707,
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
        cls.user_proof = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, owner=cls.user_session.user.user_id
        )
        cls.proof_2 = ProofFactory()
        cls.data = {
            **PRICE_8001505005707,
            "location_osm_id": 652825274,
            "location_osm_type": "NODE",
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
        self.assertEqual(response.data["price"], 15.00)
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["date"], "2024-01-01")
        self.assertTrue("source" not in response.data)
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
        # with proof, product & location
        self.assertEqual(response.data["proof"]["id"], self.user_proof.id)
        self.assertEqual(response.data["product"]["code"], "8001505005707")
        self.assertEqual(response.data["location"]["osm_id"], 652825274)
        p = Price.objects.last()
        self.assertEqual(p.source, "API")  # default value

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
            **PRICE_8001505005707, owner=cls.user_session_1.user.user_id
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
            **PRICE_8001505005707, owner=cls.user_session_1.user.user_id
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
