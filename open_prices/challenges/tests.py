from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

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

    @freeze_time("2025-01-01")
    def test_challenge_set_status(self):
        challenge_draft = ChallengeFactory(is_published=False)
        self.assertEqual(challenge_draft.status, "DRAFT")
        challenge_upcoming = ChallengeFactory(
            is_published=True, start_date="2025-01-20", end_date="2025-02-20"
        )
        self.assertEqual(challenge_upcoming.status, "UPCOMING")
        challenge_ongoing = ChallengeFactory(
            is_published=True, start_date="2024-12-30", end_date="2025-01-30"
        )
        self.assertEqual(challenge_ongoing.status, "ONGOING")
        challenge_completed = ChallengeFactory(
            is_published=True, start_date="2024-06-30", end_date="2024-07-30"
        )
        self.assertEqual(challenge_completed.status, "COMPLETED")


class ChallengeQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.challenge_archived = ChallengeFactory(
            is_published=True, start_date="2024-06-30", end_date="2024-07-30"
        )
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True, start_date="2024-12-30", end_date="2025-01-30"
        )
        cls.challenge_upcoming = ChallengeFactory(
            is_published=False, start_date="2025-01-20", end_date="2025-02-20"
        )

    def test_published(self):
        self.assertEqual(Challenge.objects.count(), 3)
        self.assertEqual(Challenge.objects.published().count(), 2)
