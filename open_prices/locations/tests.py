from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.locations.models import Location
from open_prices.prices.factories import PriceFactory

LOCATION_NODE_652825274 = {
    "osm_id": 652825274,
    "osm_type": "NODE",
    "osm_name": "Monoprix",
    "osm_display_name": "Monoprix, Boulevard Joseph Vallier, Secteur 1, Grenoble, Isère, Auvergne-Rhône-Alpes, France métropolitaine, 38000, France",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
}

LOCATION_NODE_1392117416 = {
    "osm_id": 1392117416,
    "osm_type": "NODE",
    "osm_name": "L'Éléfàn",
    "osm_display_name": "L'Éléfàn, 32, Avenue Marcelin Berthelot, Capuche, Secteur 4, Grenoble, Isère, Auvergne-Rhône-Alpes, France métropolitaine, 38100, France",
}


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


class LocationQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_without_price = LocationFactory(**LOCATION_NODE_652825274)
        cls.location_with_price = LocationFactory(**LOCATION_NODE_1392117416)
        PriceFactory(
            location_osm_id=cls.location_with_price.osm_id,
            location_osm_type=cls.location_with_price.osm_type,
            price=1.0,
        )

    def test_filter_full_text(self):
        self.assertEqual(Location.objects.filter_full_text("Grenoble").count(), 2)
        self.assertEqual(Location.objects.filter_full_text("Monoprix").count(), 1)
        self.assertEqual(Location.objects.filter_full_text("elefan").count(), 1)

    def test_has_prices(self):
        self.assertEqual(Location.objects.has_prices().count(), 1)

    def test_with_stats(self):
        location = Location.objects.with_stats().get(id=self.location_without_price.id)
        self.assertEqual(location.price_count_annotated, 0)
        self.assertEqual(location.price_count, 0)
        location = Location.objects.with_stats().get(id=self.location_with_price.id)
        self.assertEqual(location.price_count_annotated, 1)
        self.assertEqual(location.price_count, 1)
