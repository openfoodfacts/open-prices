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
    
    type = location_constants.TYPE_OSM  # random.choice(location_constants.TYPE_LIST)

    osm_id = factory.LazyAttributeSequence(
        lambda x, y: random.randrange(0, 10000000000)
        if x.type == location_constants.TYPE_OSM
        else None
    )
    osm_type = factory.LazyAttribute(
        lambda x: random.choice(location_constants.OSM_TYPE_LIST)
        if x.type == location_constants.TYPE_OSM
        else None
    )
    osm_name = factory.LazyAttribute(
        lambda x: factory.Faker("name")
        if x.type == location_constants.TYPE_OSM
        else None
    )
    osm_address_country = factory.LazyAttribute(
        lambda x: factory.Faker("country")
        if x.type == location_constants.TYPE_OSM
        else None
    )

    website_url = factory.LazyAttribute(
        lambda x: factory.Faker("uri")
        if x.type == location_constants.TYPE_WEBSITE
        else None
    )

    # price_count = factory.LazyAttribute(lambda l: random.randrange(0, 100))
    # user_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # product_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # proof_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
