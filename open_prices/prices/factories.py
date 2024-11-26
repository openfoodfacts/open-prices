import random
from datetime import date

import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.prices import constants as price_constants
from open_prices.prices.models import Price


class PriceFactory(DjangoModelFactory):
    class Meta:
        model = Price

    type = price_constants.TYPE_PRODUCT  # random.choice(price_constants.TYPE_LIST)

    product_code = factory.Faker("ean13")
    price = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # currency = factory.Faker("currency_symbol")
    currency = factory.fuzzy.FuzzyChoice(constants.CURRENCY_LIST)
    location_osm_id = factory.LazyAttribute(
        lambda x: random.randrange(100000, 999999999999)
    )
    location_osm_type = factory.fuzzy.FuzzyChoice(location_constants.OSM_TYPE_LIST)
    date = date.fromisoformat("2023-10-30")
