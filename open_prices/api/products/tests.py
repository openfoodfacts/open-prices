from django.test import TestCase
from django.urls import reverse

from open_prices.products.factories import ProductFactory


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
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])


class ProductListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ProductFactory(code="8001505005707", product_name="Nocciolata", price_count=15)
        ProductFactory(
            code="0022314010100", product_name="Chestnut spread 100 g", price_count=0
        )
        ProductFactory(
            code="8000215204219", product_name="Vitariz Rice Drink", price_count=50
        )

    def test_product_list_order_by(self):
        url = reverse("api:products-list") + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["results"][0]["price_count"], 50)

    def test_product_list_filter_by_code(self):
        url = reverse("api:products-list") + "?code=8001505005707"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["code"], "8001505005707")

    def test_product_list_filter_by_product_name(self):
        url = reverse("api:products-list") + "?product_name__like=rice"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["product_name"], "Vitariz Rice Drink"
        )

    def test_product_list_filter_by_price_count(self):
        # exact price_count
        url = reverse("api:products-list") + "?price_count=15"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 15)
        # lte / gte
        url = reverse("api:products-list") + "?price_count__gte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price_count"], 50)
        url = reverse("api:products-list") + "?price_count__lte=20"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["price_count"], 15)


class ProductDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(
            code="8001505005707", product_name="Nocciolata", price_count=15
        )

    def test_product_detail(self):
        # 404
        url = reverse("api:products-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # existing product
        url = reverse("api:products-detail", args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.data["id"], self.product.id)

    def test_product_detail_by_code(self):
        # 404
        url = reverse("api:products-get-by-code", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # existing product
        url = reverse("api:products-get-by-code", args=[self.product.code])
        response = self.client.get(url)
        self.assertEqual(response.data["id"], self.product.id)

    def test_product_update_not_allowed(self):
        data = {"product_name": "Nutella"}
        url = reverse("api:products-detail", args=[self.product.id])
        response = self.client.patch(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 405)

    def test_product_delete_not_allowed(self):
        url = reverse("api:products-detail", args=[self.product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)
