from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from open_prices.moderation.models import Flag, FlagReason, FlagStatus
from open_prices.prices.factories import PriceFactory
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import SessionFactory


class FlagListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.url = reverse("api:flags-list")
        # create flag
        Flag.objects.create(
            content_object=PriceFactory(),
            reason=FlagReason.WRONG_PRICE_VALUE,
            owner="tester",
            source="unittest",
        )

    def test_flag_list_authentication_errors(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session_1.token}X"},
        )
        self.assertEqual(response.status_code, 403)
        # user not moderator
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_flag_list_ok_if_moderator(self):
        # set user as moderator
        self.user_session_2.user.is_moderator = True
        self.user_session_2.user.save()
        # authenticated as moderator
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session_2.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(response.json()["items"][0]["content_type"], "PRICE")
        self.assertEqual(
            response.json()["items"][0]["reason"], FlagReason.WRONG_PRICE_VALUE
        )


class FlagListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.user_session.user.is_moderator = True
        cls.user_session.user.save()
        cls.url = reverse("api:flags-list")
        # create flags
        for reason in FlagReason.values:
            Flag.objects.create(
                content_object=PriceFactory(),
                reason=reason,
                owner="tester",
                source="unittest",
            )

    def test_flag_list_order_by(self):
        # default by id ascending
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        flag = Flag.objects.first()
        self.assertEqual(response.json()["items"][0]["id"], flag.id)
        # order by reason ascending
        response = self.client.get(
            f"{self.url}?order_by=reason",
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        reasons = [flag["reason"] for flag in response.json()["items"]]
        self.assertEqual(reasons, sorted(reasons))
        # order by status ascending
        flag = Flag.objects.last()
        flag.status = FlagStatus.CLOSED
        flag.save()
        response = self.client.get(
            f"{self.url}?order_by=status",
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["id"], flag.id)


class FlagListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.user_session.user.is_moderator = True
        cls.user_session.user.save()
        cls.url = reverse("api:flags-list")
        # create flags
        cls.flag_price_wrong_price_value = Flag.objects.create(
            content_object=PriceFactory(id=1),
            reason=FlagReason.WRONG_PRICE_VALUE,
            owner="tester",
            source="unittest",
        )
        cls.flag_price_wrong_type = Flag.objects.create(
            content_object=PriceFactory(id=2),
            reason=FlagReason.WRONG_TYPE,
            status=FlagStatus.CLOSED,
            owner="tester",
            source="unittest",
        )
        cls.flag_proof_wrong_type = Flag.objects.create(
            content_object=ProofFactory(id=3),
            reason=FlagReason.WRONG_TYPE,
            owner="tester",
            source="unittest",
        )

    def test_flag_list_filter_by_content_object(self):
        # object_id
        url = self.url + f"?object_id={self.flag_price_wrong_price_value.object_id}"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        # content_type (single)
        url = self.url + "?content_type=PRICE"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)
        url = self.url + "?content_type=PROOF"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        # content_type (multiple)
        url = self.url + "?content_type=PRICE&content_type=PROOF"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 3)

    def test_flag_list_filter_by_reason(self):
        # single
        url = self.url + f"?reason={FlagReason.WRONG_TYPE}"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)
        # multiple
        url = (
            self.url
            + f"?reason={FlagReason.WRONG_PRICE_VALUE}&reason={FlagReason.WRONG_TYPE}"
        )
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 3)

    def test_flag_list_filter_by_status(self):
        url = self.url + f"?status={FlagStatus.CLOSED}"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(
            response.json()["items"][0]["id"], self.flag_price_wrong_type.id
        )


class FlagDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.price = PriceFactory()
        cls.flag = Flag.objects.create(
            content_object=cls.price,
            reason=FlagReason.WRONG_PRICE_VALUE,
            owner="tester",
            source="unittest",
        )

    def test_flag_detail_not_allowed(self):
        self.assertRaises(
            NoReverseMatch, reverse, "api:flags-detail", args=[self.flag.id]
        )


class FlagUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.price = PriceFactory()
        cls.flag = Flag.objects.create(
            content_object=cls.price,
            reason=FlagReason.WRONG_PRICE_VALUE,
            owner="tester",
            source="unittest",
        )

    def test_flag_update_not_allowed(self):
        self.assertRaises(
            NoReverseMatch, reverse, "api:flags-detail", args=[self.flag.id]
        )


class FlagDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.price = PriceFactory()
        cls.flag = Flag.objects.create(
            content_object=cls.price,
            reason=FlagReason.WRONG_PRICE_VALUE,
            owner="tester",
            source="unittest",
        )

    def test_flag_delete_not_allowed(self):
        self.assertRaises(
            NoReverseMatch, reverse, "api:flags-detail", args=[self.flag.id]
        )
