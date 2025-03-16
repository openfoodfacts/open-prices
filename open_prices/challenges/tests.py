from django.test import TestCase

from open_prices.challenges.factories import ChallengeFactory


class ChallengeModelTestSave(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_challenge_validation(self):
        ChallengeFactory(challenge_id=1)
