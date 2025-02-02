from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import UserFactory
from open_prices.users.models import User

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
    "osm_address_city": "Grenoble",
    "osm_address_country": "France",
    "price_count": 15,
}
LOCATION_ONLINE_DECATHLON = {
    "type": location_constants.TYPE_ONLINE,
    "website_url": "https://www.decathlon.fr",
    "price_count": 15,
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
        cls.location_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_2 = LocationFactory(**LOCATION_ONLINE_DECATHLON)
        cls.proof = ProofFactory(
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            currency="EUR",
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code="0123456789100",
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            proof_id=cls.proof.id,
            price=1.0,
            currency=cls.proof.currency,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code="0123456789101",
            location_osm_id=cls.location_2.osm_id,
            location_osm_type=cls.location_2.osm_type,
            price=2.0,
            currency=cls.proof.currency,
            owner=cls.user.user_id,
        )

    def test_update_price_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.price_count, 2)  # price signals
        self.assertEqual(self.user.price_currency_count, 0)
        # update_price_count() should fix price counts
        self.user.update_price_count()
        self.assertEqual(self.user.price_count, 2)
        self.assertEqual(self.user.price_currency_count, 1)
        # bulk delete prices to skip signals
        Price.objects.filter(owner=self.user.user_id).delete()
        self.assertEqual(self.user.price_count, 2)  # should be 0
        self.assertEqual(self.user.price_currency_count, 1)  # should be 0
        # update_price_count() should fix price counts
        self.user.update_price_count()
        self.assertEqual(self.user.price_count, 0)
        self.assertEqual(self.user.price_currency_count, 0)

    def test_update_location_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.location_count, 0)
        self.assertEqual(self.user.location_type_osm_country_count, 0)
        # update_location_count() should fix location counts
        self.user.update_location_count()
        self.assertEqual(self.user.location_count, 1)  # proof locations
        self.assertEqual(self.user.location_type_osm_country_count, 1)

    def test_update_product_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.product_count, 0)
        # update_product_count() should fix product counts
        self.user.update_product_count()
        self.assertEqual(self.user.product_count, 2)

    def test_update_proof_count(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.proof_count, 0)
        # update_proof_count() should fix proof counts
        self.user.update_proof_count()
        self.assertEqual(self.user.proof_count, 1)
