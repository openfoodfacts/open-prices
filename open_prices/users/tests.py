from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants
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
        cls.user_1 = UserFactory()
        cls.user_2 = UserFactory()
        cls.location_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_2 = LocationFactory(**LOCATION_ONLINE_DECATHLON)
        cls.proof_1 = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            currency="EUR",
            owner=cls.user_1.user_id,
        )
        cls.proof_2 = ProofFactory(
            type=proof_constants.TYPE_GDPR_REQUEST,
            currency="USD",
            owner_consumption=True,
            owner=cls.user_1.user_id,
        )
        PriceFactory(
            product_code="0123456789100",
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            proof_id=cls.proof_1.id,
            price=1.0,
            currency=cls.proof_1.currency,
            owner=cls.user_1.user_id,
        )
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:apples",
            price_per=price_constants.PRICE_PER_UNIT,
            location_osm_id=cls.location_2.osm_id,
            location_osm_type=cls.location_2.osm_type,
            proof_id=cls.proof_2.id,
            price=2.0,
            currency=cls.proof_2.currency,
            owner=cls.user_1.user_id,
        )
        PriceFactory(
            product_code="0123456789101",
            location_osm_id=cls.location_1.osm_id,
            location_osm_type=cls.location_1.osm_type,
            proof_id=cls.proof_1.id,
            price=1.0,
            currency=cls.proof_1.currency,
            owner=cls.user_2.user_id,
        )

    def test_update_price_count(self):
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.price_count, 2)  # price signals
        self.assertEqual(self.user_1.price_type_product_count, 0)
        self.assertEqual(self.user_1.price_type_category_count, 0)
        self.assertEqual(self.user_1.price_kind_community_count, 0)
        self.assertEqual(self.user_1.price_kind_consumption_count, 0)
        self.assertEqual(self.user_1.price_in_proof_owned_count, 0)
        self.assertEqual(self.user_1.price_in_proof_not_owned_count, 0)
        self.assertEqual(self.user_1.price_not_owned_in_proof_owned_count, 0)
        # update_price_count() should fix price counts
        self.user_1.update_price_count()
        self.assertEqual(self.user_1.price_count, 2)
        self.assertEqual(self.user_1.price_type_product_count, 1)
        self.assertEqual(self.user_1.price_type_category_count, 1)
        self.assertEqual(self.user_1.price_kind_community_count, 1)
        self.assertEqual(self.user_1.price_kind_consumption_count, 1)
        self.assertEqual(self.user_1.price_in_proof_owned_count, 2)
        self.assertEqual(self.user_1.price_in_proof_not_owned_count, 0)
        self.assertEqual(self.user_1.price_not_owned_in_proof_owned_count, 1)
        # bulk delete user's prices to skip signals
        Price.objects.filter(owner=self.user_1.user_id).delete()
        self.assertEqual(self.user_1.price_count, 2)  # should be 0
        self.assertEqual(self.user_1.price_type_product_count, 1)
        self.assertEqual(self.user_1.price_type_category_count, 1)
        self.assertEqual(self.user_1.price_kind_community_count, 1)
        self.assertEqual(self.user_1.price_kind_consumption_count, 1)
        self.assertEqual(self.user_1.price_in_proof_owned_count, 2)
        self.assertEqual(self.user_1.price_in_proof_not_owned_count, 0)
        self.assertEqual(self.user_1.price_not_owned_in_proof_owned_count, 1)
        # update_price_count() should fix price counts
        self.user_1.update_price_count()
        self.assertEqual(self.user_1.price_count, 0)
        self.assertEqual(self.user_1.price_type_product_count, 0)
        self.assertEqual(self.user_1.price_type_category_count, 0)
        self.assertEqual(self.user_1.price_kind_community_count, 0)
        self.assertEqual(self.user_1.price_kind_consumption_count, 0)
        self.assertEqual(self.user_1.price_in_proof_owned_count, 0)
        self.assertEqual(self.user_1.price_in_proof_not_owned_count, 0)
        self.assertEqual(
            self.user_1.price_not_owned_in_proof_owned_count, 1
        )  # price from another user
        # stats for user_2
        self.user_2.refresh_from_db()
        self.user_2.update_price_count()
        self.assertEqual(self.user_2.price_count, 1)
        self.assertEqual(self.user_2.price_type_product_count, 1)
        self.assertEqual(self.user_2.price_type_category_count, 0)
        self.assertEqual(self.user_2.price_kind_community_count, 1)
        self.assertEqual(self.user_2.price_kind_consumption_count, 0)
        self.assertEqual(self.user_2.price_in_proof_owned_count, 0)
        self.assertEqual(self.user_2.price_in_proof_not_owned_count, 1)
        self.assertEqual(self.user_2.price_not_owned_in_proof_owned_count, 0)

    def test_update_location_count(self):
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.location_count, 0)
        self.assertEqual(self.user_1.location_type_osm_country_count, 0)
        # update_location_count() should fix location counts
        self.user_1.update_location_count()
        self.assertEqual(self.user_1.location_count, 1)  # proof locations
        self.assertEqual(self.user_1.location_type_osm_country_count, 1)

    def test_update_product_count(self):
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.product_count, 0)
        # update_product_count() should fix product counts
        self.user_1.update_product_count()
        self.assertEqual(self.user_1.product_count, 1)

    def test_update_proof_count(self):
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.proof_count, 0)
        self.assertEqual(self.user_1.proof_kind_community_count, 0)
        self.assertEqual(self.user_1.proof_kind_consumption_count, 0)
        # update_proof_count() should fix proof counts
        self.user_1.update_proof_count()
        self.assertEqual(self.user_1.proof_count, 2)
        self.assertEqual(self.user_1.proof_kind_community_count, 1)
        self.assertEqual(self.user_1.proof_kind_consumption_count, 1)

    def test_update_other_count(self):
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.currency_count, 0)
        self.assertEqual(self.user_1.year_count, 0)
        # update_other_count() should fix other counts
        self.user_1.update_other_count()
        self.assertEqual(self.user_1.currency_count, 2)
        self.assertEqual(self.user_1.year_count, 1)
