from django.test import TestCase

from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.users.factories import UserFactory
from open_prices.users.models import User

LOCATION_NODE_652825274 = {
    "osm_id": 652825274,
    "osm_type": "NODE",
    "osm_name": "Monoprix",
}


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
        cls.location = LocationFactory(**LOCATION_NODE_652825274)
        PriceFactory(
            owner=cls.user.user_id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=1.0,
        )
        PriceFactory(
            owner=cls.user.user_id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=2.0,
        )

    def test_update_price_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.price_count, 2)
        # bulk delete prices to skip signals
        Price.objects.filter(owner=self.user).delete()
        self.assertEqual(self.user.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.user.update_price_count()
        self.assertEqual(self.user.price_count, 0)

    def test_update_location_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.location_count, 0)
        # update_location_count() should fix location_count
        self.user.update_location_count()
        self.assertEqual(self.user.location_count, 1)
