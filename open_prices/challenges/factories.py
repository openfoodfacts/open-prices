from factory.django import DjangoModelFactory

from open_prices.challenges.models import Challenge


class ChallengeFactory(DjangoModelFactory):
    class Meta:
        model = Challenge

    title = "Nutella Challenge"
    icon = "🌰"
    subtitle = "(and other hazelnut spreads)"
    categories = ["en:hazelnut-spreads"]
    example_proof_url = "https://prices.openfoodfacts.org/img/0029/nCWeCVnpQJ.webp"
