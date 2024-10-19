from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import UserFactory

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
}
LOCATION_ONLINE_DECATHLON = {
    "type": location_constants.TYPE_ONLINE,
    "website_url": "https://www.decathlon.fr/",
}


class LocationModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_location_osm_id_type_validation(self):
        # both osm_id & osm_type should be set
        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_OSM,
            osm_id=None,
            osm_type=None,
        )
        # osm_id
        for LOCATION_OSM_ID_OK in location_constants.OSM_ID_OK_LIST:
            with self.subTest(osm_id=LOCATION_OSM_ID_OK):
                LocationFactory(
                    type=location_constants.TYPE_OSM,
                    osm_id=LOCATION_OSM_ID_OK,
                    osm_type=location_constants.OSM_TYPE_NODE,
                )
        for LOCATION_OSM_ID_NOT_OK in location_constants.OSM_ID_NOT_OK_LIST:
            with self.subTest(osm_id=LOCATION_OSM_ID_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    LocationFactory,
                    type=location_constants.TYPE_OSM,
                    osm_id=LOCATION_OSM_ID_NOT_OK,
                    osm_type=location_constants.OSM_TYPE_NODE,
                )
        # osm_type
        for LOCATION_OSM_TYPE_OK in location_constants.OSM_TYPE_OK_LIST:
            with self.subTest(osm_type=LOCATION_OSM_TYPE_OK):
                LocationFactory(
                    type=location_constants.TYPE_OSM,
                    osm_id=6509705997,
                    osm_type=LOCATION_OSM_TYPE_OK,
                )
        for LOCATION_OSM_TYPE_NOT_OK in location_constants.OSM_TYPE_NOT_OK_LIST:
            with self.subTest(osm_type=LOCATION_OSM_TYPE_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    LocationFactory,
                    type=location_constants.TYPE_OSM,
                    osm_id=6509705997,
                    osm_type=LOCATION_OSM_TYPE_NOT_OK,
                )
        # unique constraint
        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_OSM,
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_OK_LIST[0],
        )

    def test_location_decimal_truncate_on_create(self):
        location = LocationFactory(
            **LOCATION_OSM_NODE_652825274,
            osm_lat="45.1805534",
            osm_lon="5.7153387000",  # will be truncated
            price_count=15,
        )
        self.assertEqual(location.osm_lat, Decimal("45.1805534"))
        self.assertEqual(location.osm_lon, Decimal("5.7153387"))

    def test_location_online_validation(self):
        # website_url should be set
        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_ONLINE,
            website_url=None,
        )
        # no osm data should be passed
        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_ONLINE,
            website_url=location_constants.WEBSITE_URL_OK_LIST[0],
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_OK_LIST[0],
        )
        # ok
        for WEBSITE_URL in location_constants.WEBSITE_URL_OK_LIST:
            with self.subTest(website_url=WEBSITE_URL):
                LocationFactory(
                    type=location_constants.TYPE_ONLINE, website_url=WEBSITE_URL
                )
        # unique constraint
        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_ONLINE,
            website_url=location_constants.WEBSITE_URL_OK_LIST[0],
        )


class LocationQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_with_price = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_without_price = LocationFactory(**LOCATION_ONLINE_DECATHLON)
        PriceFactory(
            location_osm_id=cls.location_with_price.osm_id,
            location_osm_type=cls.location_with_price.osm_type,
            price=1.0,
        )

    def test_has_type_osm(self):
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Location.objects.has_type_osm().count(), 1)

    def test_has_prices(self):
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Location.objects.has_prices().count(), 1)

    def test_with_stats(self):
        location = Location.objects.with_stats().get(id=self.location_without_price.id)
        self.assertEqual(location.price_count_annotated, 0)
        self.assertEqual(location.price_count, 0)
        location = Location.objects.with_stats().get(id=self.location_with_price.id)
        self.assertEqual(location.price_count_annotated, 1)
        self.assertEqual(location.price_count, 1)


class LocationPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_2 = UserFactory()
        cls.location = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.proof = ProofFactory(
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            owner=cls.user.user_id,
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
            product_code="0123456789101",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=2.0,
            owner=cls.user_2.user_id,
        )
        PriceFactory(
            product_code=None,
            category_tag="en:tomatoes",
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
            owner=cls.user_2.user_id,
        )

    def test_update_price_count(self):
        self.location.refresh_from_db()
        self.assertEqual(self.location.price_count, 3)  # price post_save
        # bulk delete prices to skip signals
        self.location.prices.all().delete()
        self.assertEqual(self.location.price_count, 3)  # should be 0
        # update_price_count() should fix price_count
        self.location.update_price_count()
        self.assertEqual(self.location.price_count, 0)  # all deleted

    def test_update_user_count(self):
        self.location.refresh_from_db()
        self.assertEqual(self.location.user_count, 0)
        # update_user_count() should fix user_count
        self.location.update_user_count()
        self.assertEqual(self.location.user_count, 2)

    def test_update_product_count(self):
        self.location.refresh_from_db()
        self.assertEqual(self.location.product_count, 0)
        # update_product_count() should fix product_count
        self.location.update_product_count()
        self.assertEqual(self.location.product_count, 2)

    def test_update_proof_count(self):
        self.location.refresh_from_db()
        self.assertEqual(self.location.proof_count, 0)
        # update_proof_count() should fix location_count
        self.location.update_proof_count()
        self.assertEqual(self.location.proof_count, 1)
