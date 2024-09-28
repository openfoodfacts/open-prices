from django.urls import reverse
from rest_framework.test import APITestCase

from open_prices.stats.models import TotalStats


class StatsTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:stats")

    def test_get_total_stats(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json().keys()), len(TotalStats.COUNT_FIELDS) + 1)
