from django.core.exceptions import ValidationError
from django.test import TestCase

from open_prices.challenges.factories import ChallengeFactory


class ChallengeModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_challenge_date_validation(self):
        ChallengeFactory(start_date=None, end_date=None)
        ChallengeFactory(start_date=None, end_date="2024-06-30")
        ChallengeFactory(start_date="2024-06-30", end_date=None)
        ChallengeFactory(start_date="2024-06-30", end_date="2024-07-05")
        ChallengeFactory(start_date="2024-06-30", end_date="2024-06-30")
        self.assertRaises(
            ValidationError,
            ChallengeFactory,
            start_date="2024-06-30",
            end_date="2024-06-29",
        )
