from django.test import TestCase

from open_prices.common.managers import ApproximateCountQuerySet
from open_prices.products.factories import ProductFactory
from open_prices.products.models import Product


class ApproximateCountTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for _ in range(10):
            ProductFactory()

    def test_approximate_count_without_filters(self):
        count = Product.objects.count()
        self.assertGreaterEqual(count, 0)
        self.assertIsInstance(count, int)

    def test_exact_count_with_filters(self):
        ProductFactory(price_count=100)
        count = Product.objects.filter(price_count=100).count()
        self.assertEqual(count, 1)

    def test_queryset_instance(self):
        queryset = Product.objects.all()
        self.assertIsInstance(queryset, ApproximateCountQuerySet)

    def test_count_consistency(self):
        count1 = Product.objects.count()
        count2 = Product.objects.count()
        self.assertEqual(count1, count2)

    def test_filtered_count_accuracy(self):
        ProductFactory(price_count=10)
        ProductFactory(price_count=10)
        ProductFactory(price_count=20)

        count = Product.objects.filter(price_count=10).count()
        self.assertEqual(count, 2)

        count = Product.objects.filter(price_count=20).count()
        self.assertEqual(count, 1)
