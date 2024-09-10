from django.test import TestCase

from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
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


class UserPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        PriceFactory(owner=cls.user.user_id, price=1.0)
        PriceFactory(owner=cls.user.user_id, price=2.0)

    def test_update_price_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.price_count, 2)
        # bulk delete prices to skip signals
        Price.objects.filter(owner=self.user).delete()
        self.assertEqual(self.user.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.user.update_price_count()
        self.assertEqual(self.user.price_count, 0)
