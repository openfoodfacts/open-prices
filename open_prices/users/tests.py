from django.test import TestCase

from open_prices.prices.factories import PriceFactory
from open_prices.users.factories import UserFactory
from open_prices.users.models import User


class UserQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_without_price = UserFactory()
        cls.user_with_price = UserFactory()
        PriceFactory(owner=cls.user_with_price.user_id, price=1.0)

    def test_has_prices(self):
        self.assertEqual(User.objects.has_prices().count(), 1)
