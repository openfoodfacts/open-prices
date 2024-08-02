from django.test import TestCase
from django.urls import reverse

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof
from open_prices.users.factories import SessionFactory


class ProofListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(price_count=15, owner=cls.user_session.user.user_id)
        ProofFactory(price_count=0)
        ProofFactory(price_count=50)

    def test_proof_list(self):
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.user_session.token}X"}
        )
        self.assertEqual(response.status_code, 403)
        # authenticated
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.user_session.token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.proof.id)


class ProofDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.proof = ProofFactory(
            currency="EUR", price_count=15, owner=cls.user_session_1.user.user_id
        )
        cls.url = reverse("api:proofs-detail", args=[cls.proof.id])

    def test_proof_detail(self):
        # 404
        url = reverse("api:proofs-detail", args=[999])
        response = self.client.get(
            url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 404)
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}X"}
        )
        self.assertEqual(response.status_code, 403)
        # authenticated
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.proof.id)


class ProofCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-upload")
        cls.user_session = SessionFactory()
        # cls.data = {}

    def test_proof_create(self):
        data = {
            "file": open("filename.webp", "rb"),
            "type": proof_constants.TYPE_RECEIPT,
            "currency": "EUR",
            "price_count": 15,
            "source": "test",
        }
        # anonymous
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.post(
            self.url,
            data,
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
        )
        self.assertEqual(response.status_code, 403)
        # authenticated
        response = self.client.post(
            self.url,
            data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["price_count"], 0)  # ignored
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
        self.assertTrue("source" not in response.data)
        p = Proof.objects.last()
        self.assertIsNone(p.source)  # ignored
        for app_name in ["", "test app"]:
            # with empty app_name
            response = self.client.post(
                self.url + f"?app_name={app_name}",
                data,
                headers={"Authorization": f"Bearer {self.user_session.token}"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertTrue("source" not in response.data)
            p = Proof.objects.last()
            self.assertEqual(p.source, app_name)


class ProofUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.proof = ProofFactory(
            currency="EUR", price_count=15, owner=cls.user_session_1.user.user_id
        )
        cls.url = reverse("api:proofs-detail", args=[cls.proof.id])
        cls.data = {"currency": "USD", "price_count": 20}

    def test_proof_update(self):
        # anonymous
        response = self.client.patch(
            self.url, self.data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}X"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        # not proof owner
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_2.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)  # 403 ?
        # authenticated
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["currency"], "USD")
        self.assertEqual(Proof.objects.get(id=self.proof.id).price_count, 15)  # ignored


class ProofDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.proof = ProofFactory(
            currency="EUR", price_count=15, owner=cls.user_session_1.user.user_id
        )
        cls.url = reverse("api:proofs-detail", args=[cls.proof.id])

    def test_proof_delete(self):
        # anonymous
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}X"}
        )
        self.assertEqual(response.status_code, 403)
        # not proof owner
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_2.token}"}
        )
        self.assertEqual(response.status_code, 404)  # 403 ?
        # authenticated
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertEqual(
            Proof.objects.filter(owner=self.user_session_1.user.user_id).count(), 0
        )
