from django.db import IntegrityError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.products import constants as product_constants
from open_prices.products.factories import ProductFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import PriceTagFactory, ProofFactory
from open_prices.stats.models import TotalStats
from open_prices.users.factories import UserFactory

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_address_country": "France",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
    "price_count": 15,
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
        cls.location = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_2 = LocationFactory()
        ProductFactory(code="0123456789100", source=product_constants.SOURCE_OFF)
        cls.proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            currency="EUR",
            date="2024-06-30",
            owner=cls.user.user_id,
            source="Open Prices Web App",
        )
        cls.proof_receipt = ProofFactory(
            type=proof_constants.TYPE_RECEIPT,
            location_osm_id=cls.location_2.osm_id,
            location_osm_type=cls.location_2.osm_type,
            currency="EUR",
            owner_consumption=True,
            owner=cls.user_2.user_id,
        )
        cls.proof_gdpr_request = ProofFactory(
            type=proof_constants.TYPE_GDPR_REQUEST,
            currency="EUR",
            owner_consumption=True,
            owner=cls.user_2.user_id,
            source="API",
        )
        cls.price = PriceFactory(
            product_code="0123456789100",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            proof_id=cls.proof_price_tag.id,
            price=1.0,
            currency=cls.proof_price_tag.currency,
            date=cls.proof_price_tag.date,
            owner=cls.user.user_id,
            source="Open Prices Web App",
        )
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            labels_tags=["en:organic"],
            origins_tags=["en:france"],
            price=3,
            currency="EUR",
            price_per=price_constants.PRICE_PER_KILOGRAM,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code="0123456789101",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            proof_id=cls.proof_gdpr_request.id,
            price=2.0,
            currency=cls.proof_gdpr_request.currency,
            date="2025-01-01",
            owner=cls.user_2.user_id,
            source="API",
        )
        PriceTagFactory(proof=cls.proof_price_tag, status=None)
        PriceTagFactory(
            proof=cls.proof_price_tag,
            price=cls.price,
            status=proof_constants.PriceTagStatus.linked_to_price.value,
        )

    def test_update_price_stats(self):
        self.assertEqual(self.total_stats.price_count, 0)
        self.assertEqual(self.total_stats.price_type_product_code_count, 0)
        self.assertEqual(self.total_stats.price_type_category_tag_count, 0)
        self.assertEqual(self.total_stats.price_with_discount_count, 0)
        self.assertEqual(self.total_stats.price_currency_count, 0)
        self.assertEqual(self.total_stats.price_year_count, 0)
        self.assertEqual(self.total_stats.price_location_country_count, 0)
        self.assertEqual(self.total_stats.price_type_group_community_count, 0)
        self.assertEqual(self.total_stats.price_type_group_consumption_count, 0)
        self.assertEqual(self.total_stats.price_source_web_count, 0)
        self.assertEqual(self.total_stats.price_source_mobile_count, 0)
        self.assertEqual(self.total_stats.price_source_api_count, 0)
        self.assertEqual(self.total_stats.price_source_other_count, 0)
        # update_price_stats() will update price_counts
        self.total_stats.update_price_stats()
        self.assertEqual(self.total_stats.price_count, 3)
        self.assertEqual(self.total_stats.price_type_product_code_count, 2)
        self.assertEqual(self.total_stats.price_type_category_tag_count, 1)
        self.assertEqual(self.total_stats.price_with_discount_count, 0)
        self.assertEqual(self.total_stats.price_currency_count, 1)
        self.assertEqual(self.total_stats.price_year_count, 3)  # None included
        self.assertEqual(self.total_stats.price_location_country_count, 1)
        self.assertEqual(self.total_stats.price_type_group_community_count, 1)
        self.assertEqual(self.total_stats.price_type_group_consumption_count, 1)
        self.assertEqual(self.total_stats.price_source_web_count, 1)
        self.assertEqual(self.total_stats.price_source_mobile_count, 0)
        self.assertEqual(self.total_stats.price_source_api_count, 1)
        self.assertEqual(self.total_stats.price_source_other_count, 1)

    def test_update_product_stats(self):
        self.assertEqual(self.total_stats.product_count, 0)
        self.assertEqual(self.total_stats.product_source_off_count, 0)
        self.assertEqual(self.total_stats.product_with_price_count, 0)
        self.assertEqual(self.total_stats.product_source_off_with_price_count, 0)
        # update_product_stats() will update product_counts
        self.total_stats.update_product_stats()
        self.assertEqual(self.total_stats.product_count, 2)
        self.assertEqual(self.total_stats.product_source_off_count, 1)
        self.assertEqual(self.total_stats.product_with_price_count, 2)
        self.assertEqual(self.total_stats.product_source_off_with_price_count, 1)

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
        self.assertEqual(self.total_stats.proof_type_gdpr_request_count, 0)
        self.assertEqual(self.total_stats.proof_type_shop_import_count, 0)
        self.assertEqual(self.total_stats.proof_type_group_community_count, 0)
        self.assertEqual(self.total_stats.proof_type_group_consumption_count, 0)
        self.assertEqual(self.total_stats.proof_source_web_count, 0)
        self.assertEqual(self.total_stats.proof_source_mobile_count, 0)
        self.assertEqual(self.total_stats.proof_source_api_count, 0)
        self.assertEqual(self.total_stats.proof_source_other_count, 0)
        # update_proof_stats() will update proof_counts
        self.total_stats.update_proof_stats()
        self.assertEqual(self.total_stats.proof_count, 3)
        self.assertEqual(self.total_stats.proof_with_price_count, 2)
        self.assertEqual(self.total_stats.proof_type_price_tag_count, 1)
        self.assertEqual(self.total_stats.proof_type_receipt_count, 1)
        self.assertEqual(self.total_stats.proof_type_gdpr_request_count, 1)
        self.assertEqual(self.total_stats.proof_type_shop_import_count, 0)
        self.assertEqual(self.total_stats.proof_type_group_community_count, 1)
        self.assertEqual(self.total_stats.proof_type_group_consumption_count, 2)
        self.assertEqual(self.total_stats.proof_source_web_count, 1)
        self.assertEqual(self.total_stats.proof_source_mobile_count, 0)
        self.assertEqual(self.total_stats.proof_source_api_count, 1)
        self.assertEqual(self.total_stats.proof_source_other_count, 1)

    def test_update_price_tag_stats(self):
        self.assertEqual(self.total_stats.price_tag_count, 0)
        self.assertEqual(self.total_stats.price_tag_status_unknown_count, 0)
        self.assertEqual(self.total_stats.price_tag_status_linked_to_price_count, 0)
        # update_price_tag_stats() will update price_tag_counts
        self.total_stats.update_price_tag_stats()
        self.assertEqual(self.total_stats.price_tag_count, 2)
        self.assertEqual(self.total_stats.price_tag_status_unknown_count, 1)
        self.assertEqual(self.total_stats.price_tag_status_linked_to_price_count, 1)

    def test_update_user_stats(self):
        self.assertEqual(self.total_stats.user_count, 0)
        self.assertEqual(self.total_stats.user_with_price_count, 0)
        # update_user_stats() will update user_counts
        self.total_stats.update_user_stats()
        self.assertEqual(self.total_stats.user_count, 2)
        self.assertEqual(self.total_stats.user_with_price_count, 2)
