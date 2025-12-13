from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from open_prices.challenges import constants as challenge_constants
from open_prices.challenges.factories import ChallengeFactory
from open_prices.challenges.models import Challenge


class ChallengeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:challenges-list")
        cls.challenge_1 = ChallengeFactory()
        cls.challenge_2 = ChallengeFactory()

    def test_challenge_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(len(response.data["items"]), 2)
        self.assertEqual(
            response.data["items"][0]["id"], self.challenge_1.id
        )  # default order
        # extra fields: status, tag
        self.assertTrue("status" in response.data["items"][0])
        self.assertTrue("tag" in response.data["items"][0])


class ChallengeListPaginationApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:challenges-list")
        cls.challenge_1 = ChallengeFactory()
        cls.challenge_2 = ChallengeFactory()

    def test_challenge_list_size(self):
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
        cls.challenge_draft_upcoming = ChallengeFactory(
            is_published=False, start_date="2025-01-20", end_date="2025-02-20"
        )
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True, start_date="2024-12-30", end_date="2025-01-30"
        )
        cls.challenge_completed = ChallengeFactory(
            is_published=True, start_date="2024-06-30", end_date="2024-07-30"
        )

    def test_challenge_list_without_filter(self):
        self.assertEqual(Challenge.objects.count(), 3)
        response = self.client.get(self.url)
        self.assertEqual(response.data["total"], 3)

    def test_challenge_list_filter_by_id(self):
        response = self.client.get(self.url + "?id=" + str(self.challenge_ongoing.id))
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["id"], self.challenge_ongoing.id)

    def test_challenge_list_filter_by_start_date(self):
        response = self.client.get(self.url + "?start_date__gte=" + "2025-01-01")
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["id"], self.challenge_draft_upcoming.id
        )

    def test_challenge_list_filter_by_end_date(self):
        response = self.client.get(self.url + "?end_date__lt=" + "2025-01-01")
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["id"], self.challenge_completed.id)

    def test_challenge_list_filter_by_is_published(self):
        response = self.client.get(self.url + "?is_published=true")
        self.assertEqual(response.data["total"], 2)
        response = self.client.get(self.url + "?is_published=false")
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["id"], self.challenge_draft_upcoming.id
        )

    @freeze_time("2025-01-01")
    def test_challenge_list_filter_by_status(self):
        response = self.client.get(self.url)
        response = self.client.get(
            self.url + f"?status={challenge_constants.CHALLENGE_STATUS_DRAFT}"
        )
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["id"], self.challenge_draft_upcoming.id
        )
        response = self.client.get(
            self.url + f"?status={challenge_constants.CHALLENGE_STATUS_UPCOMING}"
        )
        self.assertEqual(response.data["total"], 0)
        # change the challenge_draft_upcoming to challenge_upcoming
        self.challenge_draft_upcoming.is_published = True
        self.challenge_draft_upcoming.save()
        response = self.client.get(
            self.url + f"?status={challenge_constants.CHALLENGE_STATUS_UPCOMING}"
        )
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["id"], self.challenge_draft_upcoming.id
        )
        response = self.client.get(
            self.url + f"?status={challenge_constants.CHALLENGE_STATUS_ONGOING}"
        )  # noqa
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["id"], self.challenge_ongoing.id)  # noqa
        response = self.client.get(
            self.url + f"?status={challenge_constants.CHALLENGE_STATUS_COMPLETED}"
        )  # noqa
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["id"], self.challenge_completed.id)  # noqa
