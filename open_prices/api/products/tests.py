from django.test import TestCase
from django.urls import reverse

from open_prices.products.factories import ProductFactory
from open_prices.users.factories import SessionFactory

PRODUCT_8001505005707 = {
    "code": "8001505005707",
    "product_name": "Nocciolata",
    "categories_tags": ["en:breakfasts", "en:spreads"],
    "labels_tags": ["en:no-gluten", "en:organic"],
    "brands_tags": ["rigoni-di-asiago"],
    "price_count": 15,
    "source": "off",
}


class ProductListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:products-list")
        ProductFactory(price_count=15)
        ProductFactory(price_count=0)
        ProductFactory(price_count=50)

    def test_product_list(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(len(response.data["items"]), 3)
        self.assertTrue("id" in response.data["items"][0])
        self.assertEqual(response.data["items"][0]["price_count"], 15)  # default order


class ProductListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:products-list")
        ProductFactory(price_count=15)
        ProductFactory(price_count=0)
        ProductFactory(price_count=50)

    def test_product_list_order_by(self):
        url = self.url + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["price_count"], 50)


class ProductListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:products-list")
        ProductFactory(**PRODUCT_8001505005707)
        ProductFactory(
            code="0022314010100", product_name="Chestnut spread 100 g", price_count=0
        )
        ProductFactory(
            code="8000215204219", product_name="Vitariz Rice Drink", price_count=50
        )

    def test_product_list_filter_by_code(self):
        url = self.url + "?code=8001505005707"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["code"], "8001505005707")

    def test_product_list_filter_by_product_name(self):
        url = self.url + "?product_name__like=rice"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["product_name"], "Vitariz Rice Drink"
        )

    def test_product_list_filter_by_tags(self):
        # categories_tags
        url = self.url + "?categories_tags__contains=en:breakfasts"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["categories_tags"],
            ["en:breakfasts", "en:spreads"],
        )
        # labels_tags
        url = self.url + "?labels_tags__contains=en:no-gluten"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["labels_tags"], ["en:no-gluten", "en:organic"]
        )
        # brands_tags
        url = self.url + "?brands_tags__contains=rigoni-di-asiago"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["brands_tags"], ["rigoni-di-asiago"])

    def test_product_list_filter_by_price_count(self):
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
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["items"][0]["price_count"], 15)

    def test_product_list_filter_by_source(self):
        # exact
        url = self.url + "?source=off"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        # isnull True / False
        url = self.url + "?source__isnull=true"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        url = self.url + "?source__isnull=false"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)


class ProductDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(**PRODUCT_8001505005707)
        cls.url = reverse("api:products-detail", args=[cls.product.id])

    def test_product_detail(self):
        # 404
        url = reverse("api:products-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "No Product matches the given query.")
        # existing product
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.product.id)

    def test_product_detail_by_code(self):
        # 404
        url = reverse("api:products-get-by-code", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "No Product matches the given query.")
        # existing product
        url = reverse("api:products-get-by-code", args=[self.product.code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.product.id)


class ProductCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.url = reverse("api:products-list")
        cls.data = {"code": "8001505005707", "product_name": "Nocciolata"}

    def test_product_create_not_allowed(self):
        # anonymous
        response = self.client.post(
            self.url, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)  # 405 ?
        # authenticated
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 405)


class ProductUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.product = ProductFactory(**PRODUCT_8001505005707)
        cls.url = reverse("api:products-detail", args=[cls.product.id])
        cls.data = {"product_name": "Nutella"}

    def test_product_update_not_allowed(self):
        # anonymous
        response = self.client.patch(
            self.url, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)  # 405 ?
        # authenticated
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 405)


class ProductDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.product = ProductFactory(**PRODUCT_8001505005707)
        cls.url = reverse("api:products-detail", args=[cls.product.id])

    def test_product_delete_not_allowed(self):
        # anonymous
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)  # 405 ?
        # authenticated
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session.token}"}
        )
        self.assertEqual(response.status_code, 405)


class ProductOffCreateOrUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.product = ProductFactory(**PRODUCT_8001505005707)
        cls.url = reverse(
            "api:products-create-or-update-in-off", args=[cls.product.code]
        )

    def test_product_off_create_or_update(self):
        # anonymous
        response = self.client.post(self.url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        # authenticated
        # response = self.client.post(
        #     self.url,
        #     {},
        #     headers={"Authorization": f"Bearer {self.user_session.token}"},
        #     content_type="application/json",
        # )
        # self.assertEqual(response.status_code, 200)


class ProductOffUploadImageApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.product = ProductFactory(**PRODUCT_8001505005707)
        cls.url = reverse("api:products-upload-image-in-off", args=[cls.product.code])

    def test_product_off_upload_image(self):
        # anonymous
        response = self.client.post(self.url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        # authenticated
        # response = self.client.post(
        #     self.url,
        #     {},
        #     headers={"Authorization": f"Bearer {self.user_session.token}"},
        #     content_type="application/json",
        # )
        # self.assertEqual(response.status_code, 200)
