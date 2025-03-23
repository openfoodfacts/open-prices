import datetime

import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import PriceTag, Proof, ProofPrediction, ReceiptItem


class ProofFactory(DjangoModelFactory):
    class Meta:
        model = Proof

    file_path = factory.Faker("file_path")
    mimetype = "image/jpeg"
    type = factory.fuzzy.FuzzyChoice(proof_constants.TYPE_LIST)
    # date = factory.Faker("date")
    # currency = factory.Faker("currency_symbol")
    # price_count = factory.LazyAttribute(lambda x: random.randrange(0, 100))
    # owner = factory.Faker("user_name")


class ProofPredictionFactory(DjangoModelFactory):
    class Meta:
        model = ProofPrediction

    proof = factory.SubFactory(ProofFactory)
    type = "CLASSIFICATION"
    model_name = "price_proof_classification"
    model_version = "price_proof_classification-1.0"
    created = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    data = {
        "prediction": [
            {"label": "PRICE_TAG", "score": 0.98},
            {"label": "SHELF", "score": 0.01},
            {"label": "PRODUCT_WITH_PRICE", "score": 0.004},
            {"label": "OTHER", "score": 0.002},
            {"label": "WEB_PRINT", "score": 0.002},
            {"label": "RECEIPT", "score": 0.002},
        ]
    }
    value = "SHELF"
    max_confidence = 0.98


class PriceTagFactory(DjangoModelFactory):
    class Meta:
        model = PriceTag

    proof = factory.SubFactory(ProofFactory)
    proof_prediction = factory.LazyAttribute(
        lambda x: ProofPredictionFactory(proof=x.proof)
    )
    created = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    updated = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    bounding_box = [0.1, 0.2, 0.3, 0.4]
    status = None
    created_by = None
    updated_by = None


class ReceiptItemFactory(DjangoModelFactory):
    class Meta:
        model = ReceiptItem

    proof = factory.SubFactory(ProofFactory)
    proof_prediction = factory.LazyAttribute(
        lambda x: ProofPredictionFactory(proof=x.proof)
    )
    price = None
    order = factory.Faker("pyint", min_value=1, max_value=10)
    predicted_data = {
        "product": "en:apples",
        "product_name": "Apples",
        "price": 0.98,
    }
    status = None
    created = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    updated = factory.LazyFunction(
        lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
