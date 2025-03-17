from django.test import TestCase

from open_prices.challenges.factories import ChallengeFactory


class ChallengeModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_challenge_validation(self):
        ChallengeFactory()
