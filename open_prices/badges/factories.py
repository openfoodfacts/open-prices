import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.badges import constants as badge_constants
from open_prices.badges.models import BadgeDefinition


class BadgeDefinitionFactory(DjangoModelFactory):
    class Meta:
        model = BadgeDefinition

    name = factory.Faker("name")
    metric = factory.fuzzy.FuzzyChoice(
        [choice[0] for choice in badge_constants.METRIC_CHOICES]
    )
    threshold = factory.fuzzy.FuzzyInteger(1, 100)
