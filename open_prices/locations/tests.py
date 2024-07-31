from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory


class LocationModelSaveTest(TestCase):
    def test_location_id_type_validation(self):
        # osm_id
        for LOCATION_OSM_ID_OK in [652825274, 5, 0]:
            LocationFactory(
                osm_id=LOCATION_OSM_ID_OK,
                osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in [-5, "test", None, "None"]:
            self.assertRaises(
                ValidationError,
                LocationFactory,
                osm_id=LOCATION_OSM_ID_NOT_OK,
                osm_type=location_constants.OSM_TYPE_NODE,
            )
        # osm_type
        for LOCATION_OSM_TYPE_OK in ["NODE", "WAY"]:
            LocationFactory(osm_id=652825274, osm_type=LOCATION_OSM_TYPE_OK)
        for LOCATION_OSM_TYPE_NOT_OK in ["way", "W", "test", None, "None"]:
            self.assertRaises(
                ValidationError,
                LocationFactory,
                osm_id=652825274,
                osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )
        # both osm_id & osm_type should be set
        self.assertRaises(ValidationError, LocationFactory, osm_id=None, osm_type=None)
