from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.factories import ChallengeFactory
from open_prices.challenges.models import Challenge
from open_prices.locations.factories import LocationFactory
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.factories import ProductFactory
from open_prices.proofs import constants as proof_constants
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
        cls.location = LocationFactory()
        cls.proof_in_challenge = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_id=cls.location.id,
            location_osm_id=cls.location.osm_id,
            location_osm_type=cls.location.osm_type,
            owner="user_1",
            tags=["test"],
        )
        cls.proof_not_in_challenge = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG, owner="user_1"
        )
        cls.product_8001505005707 = ProductFactory(
            **PRODUCT_8001505005707
        )  # in challenge
        # create prices before the challenge
        # (avoids setting the tag by the signal)
        with freeze_time("2025-01-01"):  # during the challenge
            PriceFactory(proof=cls.proof_not_in_challenge, owner="user_1")
            cls.price_with_existing_tag = PriceFactory(
                product_code="8001505005707",
                product=cls.product_8001505005707,
                proof=cls.proof_in_challenge,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
                owner="user_1",
                tags=["test"],
            )
            PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="en:breakfasts",
                price_per=price_constants.PRICE_PER_UNIT,
                proof=cls.proof_in_challenge,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
                owner="user_1",
            )
            PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="en:spreads",
                price_per=price_constants.PRICE_PER_UNIT,
                proof=cls.proof_in_challenge,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
                owner="user_2",
            )
            PriceFactory(
                type=price_constants.TYPE_CATEGORY,
                category_tag="en:tomatoes",
                price_per=price_constants.PRICE_PER_UNIT,
                proof=cls.proof_in_challenge,
                location_id=cls.location.id,
                location_osm_id=cls.location.osm_id,
                location_osm_type=cls.location.osm_type,
                owner="user_1",
            )
        # create the challenge afterwards
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True,
            start_date="2024-12-30",
            end_date="2025-01-30",
            categories=["en:breakfasts", "en:spreads"],
        )

    def test_set_price_tags(self):
        self.assertEqual(Price.objects.count(), 5)
        self.assertEqual(Price.objects.has_tag(self.challenge_ongoing.tag).count(), 0)
        self.challenge_ongoing.set_price_tags()
        self.assertEqual(Price.objects.has_tag(self.challenge_ongoing.tag).count(), 3)
        self.assertIn("test", self.price_with_existing_tag.tags)

    def test_set_proof_tags(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_tag(self.challenge_ongoing.tag).count(), 0)
        self.challenge_ongoing.set_price_tags()  # we need to set the price tags first
        self.challenge_ongoing.set_proof_tags()
        self.assertEqual(Proof.objects.has_tag(self.challenge_ongoing.tag).count(), 1)
        self.assertIn("test", self.proof_in_challenge.tags)

    def test_reset_price_tags(self):
        self.assertEqual(Price.objects.count(), 5)
        self.challenge_ongoing.set_price_tags()  # we need to set the price tags first
        self.assertEqual(Price.objects.has_tag(self.challenge_ongoing.tag).count(), 3)
        self.challenge_ongoing.reset_price_tags()
        self.assertEqual(Price.objects.has_tag(self.challenge_ongoing.tag).count(), 0)
        self.assertIn("test", self.price_with_existing_tag.tags)

    def test_reset_proof_tags(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.challenge_ongoing.set_price_tags()  # we need to set the price tags first
        self.challenge_ongoing.set_proof_tags()
        self.assertEqual(Proof.objects.has_tag(self.challenge_ongoing.tag).count(), 1)
        self.challenge_ongoing.reset_proof_tags()
        self.assertEqual(Proof.objects.has_tag(self.challenge_ongoing.tag).count(), 0)
        self.assertIn("test", self.proof_in_challenge.tags)

    def test_calculate_stats(self):
        self.assertIsNone(self.challenge_ongoing.stats)
        self.challenge_ongoing.set_price_tags()  # we need to set the price tags first
        self.challenge_ongoing.set_proof_tags()  # we need to set the proof tags first
        self.challenge_ongoing.calculate_stats()
        self.assertIsNotNone(self.challenge_ongoing.stats)
        self.assertEqual(self.challenge_ongoing.stats["price_count"], 3)
        self.assertEqual(self.challenge_ongoing.stats["proof_count"], 1)
        self.assertEqual(self.challenge_ongoing.stats["user_count"], 2)
        self.assertEqual(self.challenge_ongoing.stats["price_user_count"], 2)
        self.assertEqual(self.challenge_ongoing.stats["proof_user_count"], 1)
        self.assertEqual(self.challenge_ongoing.stats["price_product_count"], 1 + 2)
        self.assertEqual(self.challenge_ongoing.stats["proof_location_count"], 1)
        self.assertEqual(
            self.challenge_ongoing.stats["user_price_count_ranking"],
            [{"owner": "user_1", "count": 2}, {"owner": "user_2", "count": 1}],
        )
        self.assertEqual(
            self.challenge_ongoing.stats["user_proof_count_ranking"],
            [{"owner": "user_1", "count": 1}],
        )
        self.assertEqual(
            self.challenge_ongoing.stats["user_price_from_proof_count_ranking"],
            [{"owner": "user_1", "count": 3}],
        )
        self.assertEqual(
            self.challenge_ongoing.stats["location_price_count_ranking"],
            [
                {
                    "id": self.location.id,
                    "type": self.location.type,
                    "osm_name": self.location.osm_name,
                    "osm_address_city": self.location.osm_address_city,
                    "osm_address_country": self.location.osm_address_country,
                    "osm_address_country_code": self.location.osm_address_country_code,
                    "website_url": self.location.website_url,
                    "count": 3,
                }
            ],
        )
        self.assertEqual(
            self.challenge_ongoing.stats["location_city_price_count_ranking"],
            [
                {
                    "osm_address_city": self.location.osm_address_city,
                    "osm_address_country": self.location.osm_address_country,
                    "osm_address_country_code": self.location.osm_address_country_code,
                    "count": 3,
                }
            ],
        )
        self.assertEqual(
            self.challenge_ongoing.stats["location_country_price_count_ranking"],
            [
                {
                    "osm_address_country": self.location.osm_address_country,
                    "osm_address_country_code": self.location.osm_address_country_code,
                    "count": 3,
                }
            ],
        )
        self.assertEqual(
            self.challenge_ongoing.stats["product_price_count_ranking"],
            [
                {
                    "id": self.product_8001505005707.id,
                    "code": self.product_8001505005707.code,
                    "source": self.product_8001505005707.source,
                    "product_name": self.product_8001505005707.product_name,
                    "image_url": self.product_8001505005707.image_url,
                    "product_quantity": self.product_8001505005707.product_quantity,
                    "product_quantity_unit": self.product_8001505005707.product_quantity_unit,
                    "brands": self.product_8001505005707.brands,
                    "count": 1,
                }
            ],
        )
