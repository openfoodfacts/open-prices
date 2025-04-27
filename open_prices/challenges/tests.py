from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.factories import ChallengeFactory
from open_prices.challenges.models import Challenge


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
