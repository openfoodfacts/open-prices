from django.db import IntegrityError
from django.test import TestCase

from open_prices.locations.factories import LocationFactory
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.stats.models import TotalStats
from open_prices.users.factories import UserFactory

LOCATION_NODE_652825274 = {
    "osm_id": 652825274,
    "osm_type": "NODE",
    "osm_name": "Monoprix",
}


class TotalStatsSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.total_stats = TotalStats.get_solo()

    def test_total_stats_singleton(self):
        # cannot create another TotalStats instance
        self.assertRaises(IntegrityError, TotalStats.objects.create)


class TotalStatsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.total_stats = TotalStats.get_solo()
        cls.user = UserFactory()
        cls.user_2 = UserFactory()
        cls.location = LocationFactory(**LOCATION_NODE_652825274)
        cls.location_2 = LocationFactory()
        cls.proof = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            owner=cls.user.user_id,
        )
        cls.proof_2 = ProofFactory(
            type=proof_constants.TYPE_RECEIPT,
            location_osm_id=cls.location_2.osm_id,
            location_osm_type=cls.location_2.osm_type,
            owner=cls.user_2.user_id,
        )
        PriceFactory(
            product_code="0123456789100",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            proof_id=cls.proof.id,
            price=1.0,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code=None,
            category_tag="en:tomatoes",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            labels_tags=["en:organic"],
            origins_tags=["en:france"],
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code="0123456789101",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=2.0,
            owner=cls.user_2.user_id,
        )

    def test_update_price_stats(self):
        self.assertEqual(self.total_stats.price_count, 0)
        self.assertEqual(self.total_stats.price_type_product_code_count, 0)
        self.assertEqual(self.total_stats.price_type_category_tag_count, 0)
        # update_price_stats() will update price_counts
        self.total_stats.update_price_stats()
        self.assertEqual(self.total_stats.price_count, 3)
        self.assertEqual(self.total_stats.price_type_product_code_count, 2)
        self.assertEqual(self.total_stats.price_type_category_tag_count, 1)

    def test_update_product_stats(self):
        self.assertEqual(self.total_stats.product_count, 0)
        self.assertEqual(self.total_stats.product_with_price_count, 0)
        # update_product_stats() will update product_counts
        self.total_stats.update_product_stats()
        self.assertEqual(self.total_stats.product_count, 2)
        self.assertEqual(self.total_stats.product_with_price_count, 2)

    def test_update_location_stats(self):
        self.assertEqual(self.total_stats.location_count, 0)
        self.assertEqual(self.total_stats.location_with_price_count, 0)
        # update_location_stats() will update location_counts
        self.total_stats.update_location_stats()
        self.assertEqual(self.total_stats.location_count, 2)
        self.assertEqual(self.total_stats.location_with_price_count, 1)
        self.assertEqual(self.total_stats.location_type_osm_count, 2)
        self.assertEqual(self.total_stats.location_type_online_count, 0)

    def test_update_proof_stats(self):
        self.assertEqual(self.total_stats.proof_count, 0)
        self.assertEqual(self.total_stats.proof_with_price_count, 0)
        self.assertEqual(self.total_stats.proof_type_price_tag_count, 0)
        self.assertEqual(self.total_stats.proof_type_receipt_count, 0)
        # update_proof_stats() will update proof_counts
        self.total_stats.update_proof_stats()
        self.assertEqual(self.total_stats.proof_count, 2)
        self.assertEqual(self.total_stats.proof_with_price_count, 1)
        self.assertEqual(self.total_stats.proof_type_price_tag_count, 1)
        self.assertEqual(self.total_stats.proof_type_receipt_count, 1)
        self.assertEqual(self.total_stats.proof_type_gdpr_request_count, 0)
        self.assertEqual(self.total_stats.proof_type_shop_import_count, 0)

    def test_update_user_stats(self):
        self.assertEqual(self.total_stats.user_count, 0)
        self.assertEqual(self.total_stats.user_with_price_count, 0)
        # update_user_stats() will update user_counts
        self.total_stats.update_user_stats()
        self.assertEqual(self.total_stats.user_count, 2)
        self.assertEqual(self.total_stats.user_with_price_count, 2)
