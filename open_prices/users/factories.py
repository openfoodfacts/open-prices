import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.common.authentication import create_token
from open_prices.users.models import Session, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    user_id = factory.Faker("user_name")
    # price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # location_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))  # noqa
    # product_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))  # noqa


class SessionFactory(DjangoModelFactory):
    class Meta:
        model = Session

    user = factory.SubFactory(UserFactory)
    token = factory.LazyAttribute(lambda x: create_token(x.user.user_id))
