from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": "NODE",
    "osm_name": "Monoprix",
}
# LOCATION_OSM_NODE_6509705997 = {
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
        cls.location = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=1.0,
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=2.0,
        )
        cls.proof_receipt = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        PriceFactory(
            proof_id=cls.proof_receipt.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            price=2.0,
            currency="EUR",
            date="2024-06-30",
        )

    def test_is_type_single_shop(self):
        self.assertTrue(self.proof_price_tag.is_type_single_shop)

    def test_update_price_count(self):
        self.proof_price_tag.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)  # price post_save
        # bulk delete prices to skip signals
        self.proof_price_tag.prices.all().delete()
        self.assertEqual(self.proof_price_tag.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.proof_price_tag.update_price_count()
        self.assertEqual(self.proof_price_tag.price_count, 0)  # all deleted

    def test_update_location(self):
        # existing
        self.proof_price_tag.refresh_from_db()
        self.location.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(self.proof_price_tag.location.id, self.location.id)
        self.assertEqual(self.location.price_count, 2 + 1)
        # update location
        self.proof_price_tag.update_location(
            location_osm_id=6509705997,
            location_osm_type=location_constants.OSM_TYPE_NODE,
        )
        # check changes
        self.proof_price_tag.refresh_from_db()
        self.location.refresh_from_db()
        new_location = self.proof_price_tag.location
        self.assertNotEqual(self.location, new_location)
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(new_location.price_count, 2)
        self.assertEqual(self.location.price_count, 3 - 2)
        # update again, same location
        self.proof_price_tag.update_location(
            location_osm_id=6509705997,
            location_osm_type=location_constants.OSM_TYPE_NODE,
        )
        self.proof_price_tag.refresh_from_db()
        self.location.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(self.proof_price_tag.location.price_count, 2)

    def test_set_missing_location_from_prices(self):
        self.proof_receipt.refresh_from_db()
        self.assertTrue(self.proof_receipt.location is None)
        self.assertEqual(self.proof_receipt.price_count, 1)
        self.proof_receipt.set_missing_location_from_prices()
        self.assertEqual(self.proof_receipt.location, self.location)

    def test_set_missing_date_from_prices(self):
        self.proof_receipt.refresh_from_db()
        self.assertTrue(self.proof_receipt.date is None)
        self.assertEqual(self.proof_receipt.price_count, 1)
        self.proof_receipt.set_missing_date_from_prices()
        self.assertEqual(
            self.proof_receipt.date, self.proof_receipt.prices.first().date
        )

    def test_set_missing_currency_from_prices(self):
        self.proof_receipt.refresh_from_db()
        self.assertTrue(self.proof_receipt.currency is None)
        self.assertEqual(self.proof_receipt.price_count, 1)
        self.proof_receipt.set_missing_currency_from_prices()
        self.assertEqual(
            self.proof_receipt.currency, self.proof_receipt.prices.first().currency
        )
