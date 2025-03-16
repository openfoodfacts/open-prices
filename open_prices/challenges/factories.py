import datetime

import factory
from factory.django import DjangoModelFactory

from open_prices.challenges.constants import CHALLENGE_STATE_CURRENTLY_RUNNING
from open_prices.challenges.models import Challenge


class ChallengeFactory(DjangoModelFactory):
    class Meta:
        model = Challenge

    created = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    updated = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    challenge_id = 1
    state = CHALLENGE_STATE_CURRENTLY_RUNNING
    title = "Nutella Challenge"
    icon = "🌰"
    subtitle = "(and other hazelnut spreads)"
    start_date = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    end_date = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
        + datetime.timedelta(days=1)
    )
    categories = ["en:hazelnut-spreads"]
    example_proof_url = "https://prices.openfoodfacts.org/img/0029/nCWeCVnpQJ.webp"
