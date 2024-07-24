import random

import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    user_id = factory.Faker("user_name")
    price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
