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

    class Params:
        product_code_faker = factory.Faker("ean13")
        category_tag_faker = "en:mandarines"

    type = price_constants.TYPE_PRODUCT  # random.choice(price_constants.TYPE_LIST)

    product_code = factory.LazyAttribute(
        lambda x: (
            x.product_code_faker if x.type == price_constants.TYPE_PRODUCT else None
        )
    )
    category_tag = factory.LazyAttribute(
        lambda x: (
            x.category_tag_faker if x.type == price_constants.TYPE_CATEGORY else None
        )
    )

    price = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # currency = factory.Faker("currency_symbol")
    currency = factory.fuzzy.FuzzyChoice(constants.CURRENCY_LIST)
    location_osm_id = factory.LazyAttribute(
        lambda x: random.randrange(100000, 999999999999)
        if not hasattr(x, "location_id")
        else None
    )
    location_osm_type = factory.LazyAttribute(
        lambda x: random.choice(location_constants.OSM_TYPE_LIST)
        if not hasattr(x, "location_id")
        else None
    )
    date = date.fromisoformat("2023-10-30")
    # owner = factory.Faker("user_name")
