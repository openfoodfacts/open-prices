from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.proofs.factories import ProofFactory


class ProofModelSaveTest(TestCase):
    def test_proof_location_validation(self):
        # location_osm_id
        for LOCATION_OSM_ID_OK in [652825274, 5, 0]:
            ProofFactory(
                location_osm_id=LOCATION_OSM_ID_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in [-5, "test", None, "None"]:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=LOCATION_OSM_ID_NOT_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        # location_osm_type
        for LOCATION_OSM_TYPE_OK in ["NODE", "WAY"]:
            ProofFactory(
                location_osm_id=652825274, location_osm_type=LOCATION_OSM_TYPE_OK
            )
        for LOCATION_OSM_TYPE_NOT_OK in ["way", "W", "test", None, "None"]:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=652825274,
                location_osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )
        # both location_osm_id & location_osm_type not set
        ProofFactory(location_osm_id=None, location_osm_type=None)
