from django.test import TestCase
from django.urls import reverse

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.factories import ChallengeFactory
from open_prices.challenges.models import Challenge


class ChallengeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:challenges-list")
        cls.challenge_archived = ChallengeFactory(
            status=challenge_constants.CHALLENGE_STATUS_ARCHIVED
        )
        cls.challenge_ongoing = ChallengeFactory(
            status=challenge_constants.CHALLENGE_STATUS_ONGOING,
        )

    def test_challenge_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(len(response.data["items"]), 2)
        self.assertEqual(
            response.data["items"][0]["id"], self.challenge_archived.id
        )  # default order


class ChallengeListPaginationApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:challenges-list")
        cls.challenge_archived = ChallengeFactory(
            status=challenge_constants.CHALLENGE_STATUS_ARCHIVED
        )
        cls.challenge_ongoing = ChallengeFactory(
            status=challenge_constants.CHALLENGE_STATUS_ONGOING,
        )

    def test_price_list_size(self):
        # default
        response = self.client.get(self.url)
        for PAGINATION_KEY in ["items", "page", "pages", "size", "total"]:
            with self.subTest(PAGINATION_KEY=PAGINATION_KEY):
                self.assertTrue(PAGINATION_KEY in response.data)
        self.assertEqual(response.data["size"], 10)  # default


class ChallengeListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:challenges-list")
        cls.challenge_archived = ChallengeFactory(
            status=challenge_constants.CHALLENGE_STATUS_ARCHIVED
        )
        cls.challenge_ongoing = ChallengeFactory(
            status=challenge_constants.CHALLENGE_STATUS_ONGOING,
        )

    def test_price_list_without_filter(self):
        self.assertEqual(Challenge.objects.count(), 2)
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 2)

    def test_challenge_list_filter_by_id(self):
        response = self.client.get(self.url + "?id=" + str(self.challenge_ongoing.id))
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["id"], self.challenge_ongoing.id)

    def test_challenge_list_filter_by_status(self):
        response = self.client.get(
            self.url + "?status=" + challenge_constants.CHALLENGE_STATUS_ONGOING
        )
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["id"], self.challenge_ongoing.id)
