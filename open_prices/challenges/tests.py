from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time

from open_prices.challenges.factories import ChallengeFactory


class ChallengeModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_challenge_date_validation(self):
        ChallengeFactory(start_date=None, end_date=None)
        ChallengeFactory(start_date=None, end_date="2024-06-30")
        ChallengeFactory(start_date="2024-06-30", end_date=None)
        ChallengeFactory(start_date="2024-06-30", end_date="2024-07-30")
        ChallengeFactory(start_date="2024-06-30", end_date="2024-06-30")
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            start_date="2024-06-30",
            end_date="2024-06-29",
        )


class ChallengePropertyTest(TestCase):
    @freeze_time("2025-01-01")
    def test_status(self):
        challenge_archived = ChallengeFactory(
            start_date="2024-06-30", end_date="2024-07-30"
        )
        self.assertEqual(challenge_archived.status, "ARCHIVED")
        challenge_ongoing = ChallengeFactory(
            start_date="2024-12-30", end_date="2025-01-30"
        )
        self.assertEqual(challenge_ongoing.status, "ONGOING")
        challenge_upcoming = ChallengeFactory(
            start_date="2025-01-20", end_date="2025-02-20"
        )
        self.assertEqual(challenge_upcoming.status, "UPCOMING")
