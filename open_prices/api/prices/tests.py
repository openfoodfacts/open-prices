from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof
from open_prices.users.factories import SessionFactory

PRICE_8001505005707 = {
    "product_code": "8001505005707",
    "price": 15,
    "currency": "EUR",
    "date": "2024-01-01",
}

PRICE_APPLES = {
    "type": price_constants.TYPE_CATEGORY,
    "category_tag": "en:apples",
    "price_per": price_constants.PRICE_PER_UNIT,
    "price": 1,
    "currency": "EUR",
    "date": "2023-08-30",
}

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_address_country": "France",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
}

PRODUCT_8001505005707 = {
    "code": "8001505005707",
    "product_name": "Nocciolata",
    "categories_tags": ["en:breakfasts", "en:spreads"],
    "labels_tags": ["en:no-gluten", "en:organic"],
    "brands_tags": ["rigoni-di-asiago"],
    "price_count": 15,
}


class PriceListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        location_osm = LocationFactory(**LOCATION_OSM_NODE_652825274)
        proof = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        PriceFactory(
            price=15,
            proof_id=proof.id,
            location_id=location_osm.id,
            location_osm_id=location_osm.osm_id,
            location_osm_type=location_osm.osm_type,
        )
        PriceFactory(price=0)
        PriceFactory(price=50)

    def test_price_list(self):
        # anonymous
        # thanks to select_related, we only have 2 queries:
        # - 1 to count the number of prices
        # - 1 to get the prices and their associated proof/location/product
        with self.assertNumQueries(1 + 1):
            response = self.client.get(self.url)
            self.assertEqual(response.data["total"], 3)
            self.assertEqual(len(response.data["items"]), 3)
            self.assertTrue("id" in response.data["items"][0])
            self.assertEqual(response.data["items"][0]["price"], 15.00)  # default order
            self.assertTrue("proof" in response.data["items"][0])
            self.assertTrue("location" in response.data["items"][0])


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
        cls.user_proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG, owner=cls.user_session.user.user_id
        )
        cls.user_proof_receipt = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, owner=cls.user_session.user.user_id
        )
        cls.product = ProductFactory(**PRODUCT_8001505005707)
        cls.user_price = PriceFactory(
            **PRICE_8001505005707,
            receipt_quantity=2,
            proof_id=cls.user_proof_receipt.id,
            owner=cls.user_session.user.user_id,
            product=cls.product,
        )
        PriceFactory(
            **PRICE_APPLES,
            labels_tags=[],
            origins_tags=["en:spain"],
            proof_id=cls.user_proof_price_tag.id,
            owner=cls.user_session.user.user_id,
        )
        PriceFactory(
            **PRICE_APPLES,
            labels_tags=["en:organic"],
            origins_tags=["en:unknown"],
            owner=cls.user_session.user.user_id,
        )
        PriceFactory(
            **PRICE_APPLES,
            labels_tags=["en:organic"],
            origins_tags=["en:france"],
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
        self.assertEqual(Price.objects.count(), 5)
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 5)

    def test_price_list_filter_by_product(self):
        self.assertEqual(Price.objects.count(), 5)
        # product_code
        url = self.url + "?product_code=8001505005707"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["product_code"], "8001505005707")
        # product_id__isnull
        url = self.url + "?product_id__isnull=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["category_tag"], "en:apples")
        url = self.url + "?product_id__isnull=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        # category_tag
        url = self.url + "?category_tag=apples"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 0)
        url = self.url + "?category_tag=en:apples"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        # product__categories_tags__contains
        url = self.url + "?product__categories_tags__contains=en:breakfasts"
        # thanks to select_related, we only have 2 queries:
        # - 1 to count the number of prices
        # - 1 to get the prices (even when filtering on product fields)
        with self.assertNumQueries(1 + 1):
            response = self.client.get(url)
            self.assertEqual(response.data["total"], 1)
            self.assertTrue("product" in response.data["items"][0])

    def test_price_list_filter_by_tags(self):
        self.assertEqual(Price.objects.count(), 5)
        # labels_tags
        url = self.url + "?labels_tags__contains=en:organic"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["items"][0]["labels_tags"], ["en:organic"])
        # origins_tags
        url = self.url + "?origins_tags__contains=en:france"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        url = self.url + "?origins_tags__contains=en:unknown"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # combine
        url = (
            self.url
            + "?category_tag=en:apples&labels_tags__contains=en:organic&origins_tags__contains=en:france"
        )
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)

    def test_price_list_filter_by_price(self):
        self.assertEqual(Price.objects.count(), 5)
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
        self.assertEqual(response.data["total"], 4)
        self.assertEqual(response.data["items"][0]["price"], 15.00)
        # price_is_discounted
        url = self.url + "?price_is_discounted=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price"], 50.00)
        url = self.url + "?price_is_discounted=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 4)

    def test_price_list_filter_by_currency(self):
        self.assertEqual(Price.objects.count(), 5)
        url = self.url + "?currency=EUR"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 4)

    def test_price_list_filter_by_location(self):
        self.assertEqual(Price.objects.count(), 5)
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
        self.assertEqual(response.data["total"], 4)

    def test_price_list_filter_by_proof(self):
        self.assertEqual(Price.objects.count(), 5)
        # proof_id
        url = self.url + f"?proof_id={self.user_price.proof_id}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # proof_id__isnull
        url = self.url + "?proof_id__isnull=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        url = self.url + "?proof_id__isnull=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        # proof__type
        url = self.url + f"?proof__type={proof_constants.TYPE_RECEIPT}"
        # thanks to select_related, we only have 2 queries:
        # - 1 to count the number of prices
        # - 1 to get the prices (even when filtering on proof fields)
        with self.assertNumQueries(1 + 1):
            response = self.client.get(url)
            self.assertEqual(response.data["total"], 1)
            self.assertTrue("proof" in response.data["items"][0])
        url = self.url + f"?proof__type={proof_constants.TYPE_PRICE_TAG}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        url = (
            self.url
            + f"?proof__type={proof_constants.TYPE_RECEIPT}&proof__type={proof_constants.TYPE_PRICE_TAG}"
        )
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1 + 1)

    def test_price_list_filter_by_date(self):
        self.assertEqual(Price.objects.count(), 5)
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
        self.assertEqual(Price.objects.count(), 5)
        url = self.url + f"?owner={self.user_session.user.user_id}"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 4)

    def test_price_list_filter_by_created(self):
        self.assertEqual(Price.objects.count(), 5)
        url = self.url + "?created__gte=2024-01-01T00:00:00Z"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 5)
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

    def test_price_detail(self):
        # 404
        url = reverse("api:prices-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "No Price matches the given query.")
        # existing price
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.price.id)


class PriceCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-list")
        cls.user_session = SessionFactory()
        cls.user_proof_gdpr = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, owner=cls.user_session.user.user_id
        )
        cls.proof_price_tag = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.proof_receipt = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        cls.data = {
            **PRICE_8001505005707,
            "location_osm_id": 652825274,
            "location_osm_type": "NODE",
            "proof_id": cls.user_proof_gdpr.id,
            "source": "test",
        }

    def test_price_create_without_proof(self):
        data = self.data.copy()
        del data["proof_id"]
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

    def test_price_create_with_proof(self):
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
        self.assertEqual(response.data["receipt_quantity"], 1)  # default
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
        # with proof, product & location
        self.assertTrue("proof_id" in response.data)
        self.assertEqual(response.data["proof"]["id"], self.user_proof_gdpr.id)
        self.assertEqual(
            response.data["proof"]["price_count"], 0
        )  # not yet incremented
        self.assertEqual(Proof.objects.get(id=self.user_proof_gdpr.id).price_count, 1)
        self.assertTrue("product_id" in response.data)
        self.assertEqual(response.data["product"]["code"], "8001505005707")
        self.assertEqual(
            response.data["product"]["price_count"], 0
        )  # not yet incremented
        self.assertEqual(Product.objects.get(code="8001505005707").price_count, 1)
        self.assertTrue("location_id" in response.data)
        self.assertEqual(response.data["location"]["osm_id"], 652825274)
        self.assertEqual(
            response.data["location"]["price_count"], 0
        )  # not yet incremented
        self.assertEqual(
            Location.objects.get(osm_id=652825274, osm_type="NODE").price_count, 1
        )
        p = Price.objects.last()
        self.assertEqual(p.source, "API")  # default value

    def test_price_create_with_proof_not_owned(self):
        # not proof owner and proof is not a PRICE_TAG: NOK
        response = self.client.post(
            self.url,
            {**self.data, "proof_id": self.proof_receipt.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # not proof owner and proof is a PRICE_TAG: OK !
        response = self.client.post(
            self.url,
            {**self.data, "proof_id": self.proof_price_tag.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)

    def test_price_create_with_location_id(self):
        location_osm = LocationFactory(**LOCATION_OSM_NODE_652825274)
        location_online = LocationFactory(type=location_constants.TYPE_ONLINE)
        # with location_id, location_osm_id & location_osm_type: OK
        response = self.client.post(
            self.url,
            {**self.data, "location_id": location_osm.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["location"]["id"], location_osm.id)
        # with just location_id (OSM): NOK
        data = self.data.copy()
        del data["location_osm_id"]
        del data["location_osm_type"]
        response = self.client.post(
            self.url,
            {**data, "location_id": location_osm.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        # with just location_id (ONLINE): OK
        data = self.data.copy()
        del data["location_osm_id"]
        del data["location_osm_type"]
        response = self.client.post(
            self.url,
            {**data, "location_id": location_online.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_price_create_with_type(self):
        data = self.data.copy()
        # without type? see other tests
        # correct type
        response = self.client.post(
            self.url,
            {**data, "type": price_constants.TYPE_PRODUCT},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["type"], price_constants.TYPE_PRODUCT)
        # wrong type
        response = self.client.post(
            self.url,
            {**data, "type": price_constants.TYPE_CATEGORY},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_price_create_with_app_name(self):
        for params, result in [
            ("?", "API"),
            ("?app_name=", ""),
            ("?app_name=test app&app_version=", "test app"),
            ("?app_name=mobile&app_version=1.0", "mobile (1.0)"),
            (
                "?app_name=web&app_version=&app_page=/prices/add/multiple",
                "web - /prices/add/multiple",
            ),
        ]:
            with self.subTest(INPUT_OUPUT=(params, result)):
                response = self.client.post(
                    self.url + params,
                    self.data,
                    headers={"Authorization": f"Bearer {self.user_session.token}"},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data["source"], result)
                self.assertEqual(Price.objects.last().source, result)


class PriceUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.price_product = PriceFactory(
            **PRICE_8001505005707, owner=cls.user_session_1.user.user_id
        )
        cls.price_category = PriceFactory(
            **PRICE_APPLES, owner=cls.user_session_1.user.user_id
        )
        cls.url_price_product = reverse(
            "api:prices-detail", args=[cls.price_product.id]
        )
        cls.url_price_category = reverse(
            "api:prices-detail", args=[cls.price_category.id]
        )
        cls.data = {"currency": "USD", "product_code": "123"}

    def test_price_update_authentication_errors(self):
        # anonymous
        response = self.client.patch(
            self.url_price_product, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.patch(
            self.url_price_product,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}X"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        # not price owner
        response = self.client.patch(
            self.url_price_product,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_2.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)  # 403 ?

    def test_price_update_ok(self):
        # authenticated
        response = self.client.patch(
            self.url_price_product,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["currency"], "USD")
        self.assertEqual(
            Price.objects.get(id=self.price_product.id).product_code, "8001505005707"
        )  # ignored
        # update price category
        response = self.client.patch(
            self.url_price_category,
            {"category_tag": "en:tomatoes"},
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["category_tag"], "en:tomatoes")

    def test_price_update_type_mismatch(self):
        # cannot add 'category' fields to a 'product' price
        response = self.client.patch(
            self.url_price_product,
            {"category_tag": "en:tomatoes"},
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class PriceDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.price = PriceFactory(
            **PRICE_8001505005707, owner=cls.user_session_1.user.user_id
        )
        cls.url = reverse("api:prices-detail", args=[cls.price.id])

    def test_price_delete_authentication_errors(self):
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

    def test_price_delete_ok(self):
        # authenticated
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertEqual(
            Price.objects.filter(owner=self.user_session_1.user.user_id).count(), 0
        )


class PriceStatsApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:prices-stats")
        cls.product = ProductFactory()
        PriceFactory(
            product_code=cls.product.code,
            price=15,
            price_is_discounted=True,
            price_without_discount=20,
        )
        PriceFactory(product_code=cls.product.code, price=25)
        PriceFactory(product_code=cls.product.code, price=30)
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:apples",
            price=2,
            price_per=price_constants.PRICE_PER_KILOGRAM,
        )

    def test_price_stats(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price__count"], 4)
        self.assertEqual(response.data["price__min"], 2.00)
        self.assertEqual(response.data["price__max"], 30.00)
        self.assertEqual(response.data["price__avg"], Decimal(18.00))
        url = self.url + "?price_is_discounted=False"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price__count"], 3)
        self.assertEqual(response.data["price__avg"], Decimal(19.00))
        url = self.url + f"?price_is_discounted=false&product_code={self.product.code}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price__count"], 2)
        self.assertEqual(response.data["price__avg"], Decimal(27.50))
