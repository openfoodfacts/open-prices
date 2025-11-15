from django.test import TestCase
from django.urls import reverse

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
