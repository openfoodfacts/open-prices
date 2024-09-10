from io import BytesIO

from django.test import TestCase
from django.urls import reverse
from PIL import Image

from open_prices.locations import constants as location_constants
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory
from open_prices.proofs.models import Proof
from open_prices.users.factories import SessionFactory

PROOF = {"type": proof_constants.TYPE_RECEIPT, "currency": "EUR", "date": "2024-01-01"}


def create_fake_image() -> bytes:
    fp = BytesIO()
    image = Image.new("RGB", (100, 100))
    image.save(fp, format="WEBP")
    fp.seek(0)
    return fp


class ProofListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session.user.user_id
        )
        ProofFactory(price_count=0)
        ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=652825274,
            location_osm_type=location_constants.OSM_TYPE_NODE,
            price_count=50,
            owner=cls.user_session.user.user_id,
        )

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
        with self.assertNumQueries(4 + 1):  # thanks to select_related
            response = self.client.get(
                self.url, headers={"Authorization": f"Bearer {self.user_session.token}"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["total"], 2)  # only user's proofs
            self.assertEqual(len(response.data["items"]), 2)
            self.assertEqual(
                response.data["items"][0]["id"], self.proof.id
            )  # default order


class ProofListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session.user.user_id
        )
        ProofFactory(price_count=0)
        ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            price_count=50,
            owner=cls.user_session.user.user_id,
        )

    def test_proof_list_order_by(self):
        url = self.url + "?order_by=-price_count"
        response = self.client.get(
            url, headers={"Authorization": f"Bearer {self.user_session.token}"}
        )
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["items"][0]["price_count"], 50)


class ProofListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session.user.user_id
        )
        ProofFactory(price_count=0)
        ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            price_count=50,
            owner=cls.user_session.user.user_id,
        )

    def test_proof_list_filter_by_type(self):
        url = self.url + "?type=RECEIPT"
        response = self.client.get(
            url, headers={"Authorization": f"Bearer {self.user_session.token}"}
        )
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price_count"], 15)


class ProofDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session_1.user.user_id
        )
        cls.url = reverse("api:proofs-detail", args=[cls.proof.id])

    def test_proof_detail(self):
        # 404
        url = reverse("api:proofs-detail", args=[999])
        response = self.client.get(
            url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "No Proof matches the given query.")
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
        cls.data = {
            # "file": open("filename.webp", "rb"),
            **PROOF,
            "price_count": 15,
            "source": "test",
        }

    def test_proof_create(self):
        self.data["file"] = create_fake_image()
        # anonymous
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 403)
        # wrong token
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
        )
        self.assertEqual(response.status_code, 403)
        # authenticated
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["price_count"], 0)  # ignored
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
        self.assertTrue("source" not in response.data)
        p = Proof.objects.last()
        self.assertEqual(p.source, "API")  # default value

    def test_proof_create_with_app_name(self):
        self.data["file"] = create_fake_image()
        for app_name in ["", "test app"]:
            # with empty app_name
            response = self.client.post(
                self.url + f"?app_name={app_name}",
                self.data,
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
            **PROOF, price_count=15, owner=cls.user_session_1.user.user_id
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
            **PROOF, price_count=15, owner=cls.user_session_1.user.user_id
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
