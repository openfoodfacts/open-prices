from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import UserFactory

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_address_country": "France",
    "osm_brand": "Monoprix",
}
LOCATION_ONLINE_DECATHLON = {
    "type": location_constants.TYPE_ONLINE,
    "website_url": "https://www.decathlon.fr",
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
        # unique constraint: same osm_id + osm_type + osm_version should fail
        LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_OK_LIST[0],
            osm_version=1,
        )

        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_OSM,
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_OK_LIST[0],
            osm_version=1,
        )

        # different osm_version should be allowed (versioning support)
        LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_OK_LIST[0],
            osm_version=2,
        )

    def test_location_decimal_truncate_on_create(self):
        # input: string
        location = LocationFactory(
            **LOCATION_OSM_NODE_652825274,
            osm_lat="45.1805534",
            osm_lon="5.7153387000",  # will be truncated
            price_count=15,
        )
        self.assertEqual(location.osm_lat, Decimal("45.1805534"))
        self.assertEqual(location.osm_lon, Decimal("5.7153387"))
        # see common.utils.tests for more truncate_decimal tests (with float and Decimal inputs)

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
            website_url=location_constants.WEBSITE_URL_OK_TUPLE_LIST[0][0],
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_OK_LIST[0],
        )
        # ok
        for WEBSITE_URL_TUPLE in location_constants.WEBSITE_URL_OK_TUPLE_LIST:
            with self.subTest(website_url=WEBSITE_URL_TUPLE):
                location = LocationFactory(
                    type=location_constants.TYPE_ONLINE,
                    website_url=WEBSITE_URL_TUPLE[0],
                )
                self.assertEqual(location.website_url, WEBSITE_URL_TUPLE[1])
        # unique constraint
        self.assertRaises(
            ValidationError,
            LocationFactory,
            type=location_constants.TYPE_ONLINE,
            website_url=location_constants.WEBSITE_URL_OK_TUPLE_LIST[0][0],
        )


class LocationVersioningTest(TestCase):
    def test_same_osm_id_different_version_allowed(self):
        # first version of the location
        location_v1 = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_id=298872652,
            osm_type=location_constants.OSM_TYPE_NODE,
            osm_name="Casino",
            osm_brand="Casino",
            osm_version=16,
        )
        # second version of the same location
        location_v2 = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_id=298872652,
            osm_type=location_constants.OSM_TYPE_NODE,
            osm_name="Intermarché",
            osm_brand="Intermarché",
            osm_version=21,
        )
        # both records should exist in the database
        self.assertEqual(Location.objects.filter(osm_id=298872652).count(), 2)
        # each record should have the correct brand
        self.assertEqual(location_v1.osm_brand, "Casino")
        self.assertEqual(location_v2.osm_brand, "Intermarché")
        # each record should have a different version
        self.assertNotEqual(location_v1.osm_version, location_v2.osm_version)


class LocationQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_osm_with_price = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_online_without_price = LocationFactory(**LOCATION_ONLINE_DECATHLON)
        PriceFactory(
            location_osm_id=cls.location_osm_with_price.osm_id,
            location_osm_type=cls.location_osm_with_price.osm_type,
            price=1.0,
        )

    def test_has_type_osm(self):
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Location.objects.has_type_osm().count(), 1)

    def test_has_prices(self):
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(Location.objects.has_prices().count(), 1)

    def test_with_stats(self):
        location = Location.objects.with_stats().get(
            id=self.location_online_without_price.id
        )
        self.assertEqual(location.price_count_annotated, 0)
        self.assertEqual(location.price_count, 0)
        location = Location.objects.with_stats().get(id=self.location_osm_with_price.id)
        self.assertEqual(location.price_count_annotated, 1)
        self.assertEqual(location.price_count, 1)


class LocationQuerySetNearbyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.CENTER_LAT = 48
        cls.CENTER_LON = 2
        cls.location_osm_far = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_lat=cls.CENTER_LAT + 0.1,  # ~13km north
            osm_lon=cls.CENTER_LON + 0.1,  # ~13km east
        )
        cls.location_osm_near = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_lat=cls.CENTER_LAT + 0.01,  # ~1.3km north
            osm_lon=cls.CENTER_LON + 0.01,  # ~1.3km east
        )
        cls.location_osm_center = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_lat=cls.CENTER_LAT,
            osm_lon=cls.CENTER_LON,
        )
        cls.location_osm_no_coords = LocationFactory(
            type=location_constants.TYPE_OSM,
            osm_lat=None,
            osm_lon=None,
        )
        cls.location_online = LocationFactory(type=location_constants.TYPE_ONLINE)

    def test_nearby_radius_km_zero(self):
        self.assertEqual(Location.objects.count(), 5)
        location_nearby_qs = Location.objects.nearby(
            self.CENTER_LAT, self.CENTER_LON, radius_km=0
        )
        self.assertEqual(location_nearby_qs.count(), 1)
        self.assertEqual(location_nearby_qs.first().id, self.location_osm_center.id)
        self.assertEqual(location_nearby_qs.first().distance_km, 0)

    def test_nearby_radius_km_5(self):
        self.assertEqual(Location.objects.count(), 5)
        location_nearby_qs = Location.objects.nearby(
            self.CENTER_LAT, self.CENTER_LON, radius_km=5
        )
        self.assertEqual(location_nearby_qs.count(), 2)
        # distance_km annotated
        self.assertIsNotNone(location_nearby_qs.first().distance_km)
        # ordered by distance
        self.assertEqual(location_nearby_qs.first().id, self.location_osm_center.id)


class LocationPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_2 = UserFactory()
        cls.location_osm = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_online = LocationFactory(**LOCATION_ONLINE_DECATHLON)
        cls.proof_1 = ProofFactory(
            type=proof_constants.TYPE_RECEIPT,
            location_osm_id=cls.location_osm.osm_id,
            location_osm_type=cls.location_osm.osm_type,
            owner=cls.user.user_id,
        )
        cls.proof_2 = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location_osm.osm_id,
            location_osm_type=cls.location_osm.osm_type,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code="0123456789100",
            location_osm_id=cls.location_osm.osm_id,
            location_osm_type=cls.location_osm.osm_type,
            proof_id=cls.proof_1.id,
            price=1.0,
            owner=cls.user.user_id,
        )
        PriceFactory(
            product_code="0123456789101",
            location_osm_id=cls.location_osm.osm_id,
            location_osm_type=cls.location_osm.osm_type,
            proof_id=cls.proof_2.id,
            price=2.0,
            owner=cls.user_2.user_id,
        )
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            location_osm_id=cls.location_osm.osm_id,
            location_osm_type=cls.location_osm.osm_type,
            proof_id=cls.proof_2.id,
            price=3,
            price_per=price_constants.PRICE_PER_KILOGRAM,
            owner=cls.user_2.user_id,
        )

    def test_is_type_osm(self):
        self.assertTrue(self.location_osm.is_type_osm)
        self.assertFalse(self.location_online.is_type_osm)

    def test_is_type_online(self):
        self.assertFalse(self.location_osm.is_type_online)
        self.assertTrue(self.location_online.is_type_online)

    def test_osm_brand_logo_url(self):
        self.assertIsNotNone(self.location_osm.osm_brand_logo_url)
        self.assertIsNone(self.location_online.osm_brand_logo_url)

    def test_update_price_count(self):
        self.location_osm.refresh_from_db()
        self.assertEqual(self.location_osm.price_count, 3)  # price post_save
        # bulk delete prices to skip signals
        self.location_osm.prices.all().delete()
        self.assertEqual(self.location_osm.price_count, 3)  # should be 0
        # update_price_count() should fix price_count
        self.location_osm.update_price_count()
        self.assertEqual(self.location_osm.price_count, 0)  # all deleted

    def test_update_user_count(self):
        self.location_osm.refresh_from_db()
        self.assertEqual(self.location_osm.user_count, 0)
        # update_user_count() should fix user_count
        self.location_osm.update_user_count()
        self.assertEqual(self.location_osm.user_count, 1)  # proof owners

    def test_update_product_count(self):
        self.location_osm.refresh_from_db()
        self.assertEqual(self.location_osm.product_count, 0)
        # update_product_count() should fix product_count
        self.location_osm.update_product_count()
        self.assertEqual(self.location_osm.product_count, 2)

    def test_update_proof_count(self):
        self.location_osm.refresh_from_db()
        self.assertEqual(self.location_osm.proof_count, 2)  # proof post_save
        # bulk delete proofs to skip signals
        self.location_osm.proofs.all().delete()
        self.assertEqual(self.location_osm.proof_count, 2)  # should be 0
        # update_proof_count() should fix location_count
        self.location_osm.update_proof_count()
        self.assertEqual(self.location_osm.proof_count, 0)  # all deleted
