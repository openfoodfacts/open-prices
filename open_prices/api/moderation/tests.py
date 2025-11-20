from django.test import TestCase
from django.urls import reverse

from open_prices.moderation.models import Flag, FlagReason, FlagStatus
from open_prices.prices.factories import PriceFactory
from open_prices.proofs.factories import ProofFactory
from open_prices.users.factories import SessionFactory


class FlagListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
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
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
        )
        self.assertEqual(response.status_code, 403)
        # user not moderator
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_flag_list_ok_if_moderator(self):
        # set user as moderator
        self.user_session.user.is_moderator = True
        self.user_session.user.save()
        # authenticated as moderator
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
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

    def test_flag_list_filter_by_object_id(self):
        # object_id
        url = self.url + f"?object_id={self.flag_price_wrong_price_value.object_id}"
        response = self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)

    def test_flag_list_filter_by_content_type(self):
        # single
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
        # multiple
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
            comment="Please fix",
            owner="tester",
            source="unittest",
        )
        cls.url = reverse("api:flags-detail", args=[cls.flag.id])

    def test_flag_detail_not_allowed(self):
        # set user as moderator
        self.user_session.user.is_moderator = True
        self.user_session.user.save()
        # authenticated as moderator
        response = self.client.get(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 405)


class FlagUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.price = PriceFactory()
        cls.flag = Flag.objects.create(
            content_object=cls.price,
            reason=FlagReason.WRONG_PRICE_VALUE,
            comment="Please fix",
            owner="tester",
            source="unittest",
        )
        cls.url = reverse("api:flags-detail", args=[cls.flag.id])

    def test_flag_put_not_allowed(self):
        # set user as moderator
        self.user_session.user.is_moderator = True
        self.user_session.user.save()
        # authenticated as moderator
        response = self.client.put(
            self.url,
            data={
                "status": FlagStatus.CLOSED,
                "reason": FlagReason.WRONG_TYPE,
                "comment": "hacked",
            },
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 405)

    def test_flag_patch_authentication_errors(self):
        # anonymous
        response = self.client.patch(
            self.url,
            data={"status": FlagStatus.CLOSED},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.patch(
            self.url,
            data={"status": FlagStatus.CLOSED},
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        # user not moderator
        response = self.client.patch(
            self.url,
            data={"status": FlagStatus.CLOSED},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_flag_patch_ok_if_moderator(self):
        # set user as moderator
        self.user_session.user.is_moderator = True
        self.user_session.user.save()
        # authenticated as moderator
        response = self.client.patch(
            self.url,
            data={"status": FlagStatus.CLOSED},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlagStatus.CLOSED)

    def test_flag_patch_only_status(self):
        # set user as moderator
        self.user_session.user.is_moderator = True
        self.user_session.user.save()
        # authenticated as moderator
        # attempt to change reason and comment in same PATCH
        response = self.client.patch(
            self.url,
            data={
                "status": FlagStatus.CLOSED,
                "reason": FlagReason.WRONG_PRODUCT,
                "comment": "hacked",
            },
            headers={"Authorization": f"Bearer {self.user_session.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlagStatus.CLOSED)
        self.assertEqual(self.flag.reason, FlagReason.WRONG_PRICE_VALUE)
        self.assertEqual(self.flag.comment, "Please fix")


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
        cls.url = reverse("api:flags-detail", args=[cls.flag.id])

    def test_flag_delete_not_allowed(self):
        # set user as moderator
        self.user_session.user.is_moderator = True
        self.user_session.user.save()
        # authenticated as moderator
        response = self.client.delete(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 405)
