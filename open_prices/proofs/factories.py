import random

import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import Proof


class ProofFactory(DjangoModelFactory):
    class Meta:
        model = Proof

    type = factory.fuzzy.FuzzyChoice(proof_constants.TYPE_LIST)
    # date = factory.Faker("date")
    # currency = factory.Faker("currency_symbol")
    price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
