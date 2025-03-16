from django.test import TestCase
from django.urls import reverse

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.factories import ChallengeFactory


class ChallengeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:challenges-list")
        ChallengeFactory(
            challenge_id="1", state=challenge_constants.CHALLENGE_STATE_ARCHIVED
        )
        ChallengeFactory(
            challenge_id="2",
            state=challenge_constants.CHALLENGE_STATE_CURRENTLY_RUNNING,
        )

    def test_challenge_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(len(response.data["items"]), 2)
        self.assertFalse("challenge_id" in response.data["items"][0])
        self.assertEqual(
            response.data["items"][0]["challenge_id"], "1"
        )  # default order
