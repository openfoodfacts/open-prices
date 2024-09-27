import random

import factory
import factory.fuzzy
from django.db.models.signals import post_save
from factory.django import DjangoModelFactory

from open_prices.locations import constants as location_constants
from open_prices.locations.models import Location


@factory.django.mute_signals(post_save)
class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    osm_id = factory.Sequence(lambda x: random.randrange(0, 10000000000))
    osm_type = factory.fuzzy.FuzzyChoice(location_constants.OSM_TYPE_LIST)
    osm_name = factory.Faker("name")
    osm_address_country = factory.Faker("country")
    # price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # user_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # product_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # proof_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
