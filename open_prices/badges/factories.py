import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.badges import constants as badge_constants
from open_prices.badges.models import Badge


class BadgeFactory(DjangoModelFactory):
    class Meta:
        model = Badge

    name = factory.Faker("name")
    metric = factory.fuzzy.FuzzyChoice(
        [choice[0] for choice in badge_constants.METRIC_CHOICES]
    )
    threshold = factory.fuzzy.FuzzyInteger(1, 100)
