from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory


class LocationModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_location_id_type_validation(self):
        # both osm_id & osm_type should be set
        self.assertRaises(ValidationError, LocationFactory, osm_id=None, osm_type=None)
        # osm_id
        for LOCATION_OSM_ID_OK in location_constants.OSM_ID_OK_LIST:
            LocationFactory(
                osm_id=LOCATION_OSM_ID_OK,
                osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in location_constants.OSM_ID_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                LocationFactory,
                osm_id=LOCATION_OSM_ID_NOT_OK,
                osm_type=location_constants.OSM_TYPE_NODE,
            )
        # osm_type
        for LOCATION_OSM_TYPE_OK in location_constants.OSM_TYPE_OK_LIST:
            LocationFactory(osm_id=6509705997, osm_type=LOCATION_OSM_TYPE_OK)
        for LOCATION_OSM_TYPE_NOT_OK in location_constants.OSM_TYPE_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                LocationFactory,
                osm_id=6509705997,
                osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )
        # must be unique
        self.assertRaises(
            ValidationError,
            LocationFactory,
            osm_id=6509705997,
            osm_type=location_constants.OSM_TYPE_NODE,
        )

    def test_location_decimal_truncate_on_create(self):
        location = LocationFactory(
            osm_id=652825274,
            osm_type="NODE",
            osm_name="Monoprix",
            osm_lat="45.1805534",
            osm_lon="5.7153387000",  # will be truncated
            price_count=15,
        )
        self.assertEqual(location.osm_lat, Decimal("45.1805534"))
        self.assertEqual(location.osm_lon, Decimal("5.7153387"))
