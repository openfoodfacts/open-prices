from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof

LOCATION_NODE_652825274 = {
    "osm_id": 652825274,
    "osm_type": "NODE",
    "osm_name": "Monoprix",
}
# LOCATION_NODE_6509705997 = {
#     "osm_id": 6509705997,
#     "osm_type": "NODE",
#     "osm_name": "Carrefour",
# }


class ProofModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_proof_date_validation(self):
        for DATE_OK in [None, "2024-01-01"]:
            ProofFactory(date=DATE_OK)
        for DATE_NOT_OK in ["3000-01-01", "01-01-2000"]:
            self.assertRaises(ValidationError, ProofFactory, date=DATE_NOT_OK)

    def test_proof_location_validation(self):
        # both location_osm_id & location_osm_type not set
        ProofFactory(location_osm_id=None, location_osm_type=None)
        # location_osm_id
        for LOCATION_OSM_ID_OK in location_constants.OSM_ID_OK_LIST:
            ProofFactory(
                location_osm_id=LOCATION_OSM_ID_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in location_constants.OSM_ID_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=LOCATION_OSM_ID_NOT_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        # location_osm_type
        for LOCATION_OSM_TYPE_OK in location_constants.OSM_TYPE_OK_LIST:
            ProofFactory(
                location_osm_id=652825274, location_osm_type=LOCATION_OSM_TYPE_OK
            )
        for LOCATION_OSM_TYPE_NOT_OK in location_constants.OSM_TYPE_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=652825274,
                location_osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )


class ProofQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_without_price = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.proof_with_price = ProofFactory(type=proof_constants.TYPE_GDPR_REQUEST)
        PriceFactory(proof_id=cls.proof_with_price.id, price=1.0)

    def test_has_type_single_shop(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_type_single_shop().count(), 1)

    def test_has_prices(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_prices().count(), 1)

    def test_with_stats(self):
        proof = Proof.objects.with_stats().get(id=self.proof_without_price.id)
        self.assertEqual(proof.price_count_annotated, 0)
        self.assertEqual(proof.price_count, 0)
        proof = Proof.objects.with_stats().get(id=self.proof_with_price.id)
        self.assertEqual(proof.price_count_annotated, 1)
        self.assertEqual(proof.price_count, 1)


class ProofPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location = LocationFactory(**LOCATION_NODE_652825274)
        cls.proof = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
        )
        PriceFactory(
            proof_id=cls.proof.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=1.0,
        )
        PriceFactory(
            proof_id=cls.proof.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=2.0,
        )

    def test_is_type_single_shop(self):
        self.assertTrue(self.proof.is_type_single_shop)

    def test_update_price_count(self):
        self.proof.refresh_from_db()
        self.assertEqual(self.proof.price_count, 2)  # price post_save
        # bulk delete prices to skip signals
        self.proof.prices.all().delete()
        self.assertEqual(self.proof.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.proof.update_price_count()
        self.assertEqual(self.proof.price_count, 0)  # all deleted

    def test_update_location(self):
        # existing
        self.proof.refresh_from_db()
        self.location.refresh_from_db()
        self.assertEqual(self.proof.price_count, 2)
        self.assertEqual(self.proof.location.id, self.location.id)
        self.assertEqual(self.location.price_count, 2)
        # update location
        self.proof.update_location(
            location_osm_id=6509705997,
            location_osm_type=location_constants.OSM_TYPE_NODE,
        )
        # check changes
        self.proof.refresh_from_db()
        self.location.refresh_from_db()
        new_location = self.proof.location
        self.assertNotEqual(self.location, new_location)
        self.assertEqual(self.proof.price_count, 2)
        self.assertEqual(new_location.price_count, 2)
        self.assertEqual(self.location.price_count, 0)
        # update again, same location
        self.proof.update_location(
            location_osm_id=6509705997,
            location_osm_type=location_constants.OSM_TYPE_NODE,
        )
        self.proof.refresh_from_db()
        self.location.refresh_from_db()
        self.assertEqual(self.proof.price_count, 2)
        self.assertEqual(self.proof.location.price_count, 2)
