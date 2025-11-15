from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from open_prices.moderation.models import Flag, FlagReason, FlagStatus
from open_prices.prices.factories import PriceFactory
from open_prices.users.factories import SessionFactory


class FlagListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.url = reverse("api:flags-list")

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
                owner=cls.user_session.user.user_id,
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


class FlagDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.price = PriceFactory()
        cls.flag = Flag.objects.create(
            content_object=cls.price,
            reason=FlagReason.WRONG_PRICE_VALUE,
            owner=cls.user_session.user.user_id,
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
            owner=cls.user_session.user.user_id,
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
            owner=cls.user_session.user.user_id,
            source="unittest",
        )

    def test_flag_delete_not_allowed(self):
        self.assertRaises(
            NoReverseMatch, reverse, "api:flags-detail", args=[self.flag.id]
        )
