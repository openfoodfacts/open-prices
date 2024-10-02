import factory
import factory.fuzzy
from django.db.models.signals import post_save
from factory.django import DjangoModelFactory

from open_prices.products.models import Product


@factory.django.mute_signals(post_save)
class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    code = factory.Faker("ean13")
    product_name = factory.Faker("name")
    # price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # location_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))  # noqa
    # user_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
