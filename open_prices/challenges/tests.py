from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.factories import ChallengeFactory
from open_prices.challenges.models import Challenge
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.factories import ProductFactory
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof

PRODUCT_8001505005707 = {
    "code": "8001505005707",
    "product_name": "Nocciolata",
    "categories_tags": ["en:breakfasts", "en:spreads"],
    "labels_tags": ["en:no-gluten", "en:organic"],
    "brands_tags": ["rigoni-di-asiago"],
    "price_count": 15,
}


class ChallengeModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_challenge_date_validation(self):
        ChallengeFactory(is_published=False, start_date=None, end_date=None)
        ChallengeFactory(is_published=False, start_date=None, end_date="2024-06-30")
        ChallengeFactory(is_published=False, start_date="2024-06-30", end_date=None)
        ChallengeFactory(
            is_published=False, start_date="2024-06-30", end_date="2024-07-30"
        )
        ChallengeFactory(
            is_published=False, start_date="2024-06-30", end_date="2024-06-30"
        )
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            is_published=False,
            start_date="2024-06-30",
            end_date="2024-06-29",
        )

    def test_challenge_published_validation(self):
        ChallengeFactory(
            is_published=True,
            title="Ready",
            start_date="2024-06-30",
            end_date="2024-07-30",
        )
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            is_published=True,
            title=None,
            start_date="2024-06-30",
            end_date="2024-07-30",
        )
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            is_published=True,
            start_date=None,
            end_date=None,
        )
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            is_published=True,
            start_date="2024-06-30",
            end_date=None,
        )
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            is_published=True,
            start_date=None,
            end_date="2024-06-30",
        )


class ChallengeQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.challenge_upcoming = ChallengeFactory(
            is_published=False, start_date="2025-01-20", end_date="2025-02-20"
        )
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True, start_date="2024-12-30", end_date="2025-01-30"
        )
        cls.challenge_completed = ChallengeFactory(
            is_published=True, start_date="2024-06-30", end_date="2024-07-30"
        )

    def test_published(self):
        self.assertEqual(Challenge.objects.count(), 3)
        self.assertEqual(Challenge.objects.published().count(), 2)


class ChallengeStatusQuerySetAndPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.challenge_draft = ChallengeFactory(is_published=False)
        cls.challenge_upcoming = ChallengeFactory(
            is_published=True, start_date="2025-01-20", end_date="2025-02-20"
        )
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True, start_date="2024-12-30", end_date="2025-01-30"
        )
        cls.challenge_completed = ChallengeFactory(
            is_published=True, start_date="2024-06-30", end_date="2024-07-30"
        )

    @freeze_time("2025-01-01")
    def test_challenge_status_queryset(self):
        self.assertEqual(Challenge.objects.count(), 4)
        self.assertEqual(Challenge.objects.with_status().count(), 4)
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_DRAFT)
            .count(),
            1,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_DRAFT)
            .first(),
            self.challenge_draft,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_UPCOMING)
            .count(),
            1,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_UPCOMING)
            .first(),
            self.challenge_upcoming,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_ONGOING)
            .count(),
            1,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_ONGOING)
            .first(),
            self.challenge_ongoing,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_COMPLETED)
            .count(),
            1,
        )
        self.assertEqual(
            Challenge.objects.with_status()
            .filter(status_annotated=challenge_constants.CHALLENGE_STATUS_COMPLETED)
            .first(),
            self.challenge_completed,
        )

    @freeze_time("2025-01-01")
    def test_challenge_status_property(self):
        self.assertEqual(self.challenge_draft.status, "DRAFT")
        self.assertEqual(self.challenge_upcoming.status, "UPCOMING")
        self.assertEqual(self.challenge_ongoing.status, "ONGOING")
        self.assertEqual(self.challenge_completed.status, "COMPLETED")

    @freeze_time("2025-01-01")
    def test_challenge_is_ongoing_queryset(self):
        self.assertEqual(Challenge.objects.count(), 4)
        self.assertEqual(Challenge.objects.is_ongoing().count(), 1)


class ChallengePropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_in_challenge = ProofFactory()
        cls.proof_not_in_challenge = ProofFactory()
        cls.product_8001505005707 = ProductFactory(
            **PRODUCT_8001505005707
        )  # in challenge
        # create prices before the challenge
        # (avoids setting the tag by the signal)
        with freeze_time("2025-01-01"):  # during the challenge
            PriceFactory(proof=cls.proof_not_in_challenge)
            PriceFactory(
                product_code="8001505005707",
                product=cls.product_8001505005707,
                proof=cls.proof_in_challenge,
            )
            PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="en:breakfasts",
                price_per=price_constants.PRICE_PER_UNIT,
                proof=cls.proof_in_challenge,
            )
        # create the challenge afterwards
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True,
            start_date="2024-12-30",
            end_date="2025-01-30",
            categories=["en:breakfasts"],
        )

    def test_set_price_tags(self):
        self.assertEqual(Price.objects.count(), 3)
        self.assertEqual(Price.objects.has_tag(self.challenge_ongoing.tag).count(), 0)
        self.challenge_ongoing.set_price_tags()
        self.assertEqual(Price.objects.has_tag(self.challenge_ongoing.tag).count(), 2)

    def test_set_proof_tags(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_tag(self.challenge_ongoing.tag).count(), 0)
        self.challenge_ongoing.set_price_tags()  # we need to set the price tags first
        self.challenge_ongoing.set_proof_tags()
        self.assertEqual(Proof.objects.has_tag(self.challenge_ongoing.tag).count(), 1)
