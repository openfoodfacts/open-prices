import random

import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.products.models import Product


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    code = factory.Faker("ean13")
    product_name = factory.Faker("name")
    price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
