from decimal import Decimal
from io import BytesIO

from django.test import TestCase
from django.urls import reverse
from PIL import Image

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory, ProofPredictionFactory
from open_prices.proofs.models import Proof
from open_prices.users.factories import SessionFactory

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_lat": "45.1805534",
    "osm_lon": "5.7153387",
}
LOCATION_OSM_NODE_6509705997 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 6509705997,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Carrefour",
}
PROOF = {
    "type": proof_constants.TYPE_RECEIPT,
    "currency": "EUR",
    "date": "2024-01-01",
    "location_osm_id": LOCATION_OSM_NODE_652825274["osm_id"],
    "location_osm_type": LOCATION_OSM_NODE_652825274["osm_type"],
    "receipt_price_count": 5,
    "receipt_price_total": Decimal("45.10"),
}


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
        cls.proof_prediction = ProofPredictionFactory(
            proof=cls.proof, type="CLASSIFICATION"
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
        # all proofs are read-accessible to anyone
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 3)  # All proofs are returned
        # authenticated
        # thanks to select_related and prefetch_related, we only have 6
        # queries:
        # - 1 to get the fetch the user session
        # - 1 to update the session
        # - 1 to get the user
        # - 1 to count the number of proofs of the user
        # - 1 to get the proofs and their associated locations (select_related)
        # - 1 to get the associated proof predictions (prefetch_related)
        with self.assertNumQueries(6):
            response = self.client.get(
                self.url, headers={"Authorization": f"Bearer {self.user_session.token}"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.data
            self.assertEqual(data["total"], 3)  # only user's proofs
            self.assertEqual(len(data["items"]), 3)
            item = data["items"][0]
            self.assertEqual(item["id"], self.proof.id)  # default order
            self.assertIn("predictions", item)
            self.assertEqual(len(item["predictions"]), 1)
            prediction = item["predictions"][0]
            self.assertEqual(prediction["type"], self.proof_prediction.type)
            self.assertEqual(prediction["model_name"], self.proof_prediction.model_name)
            self.assertEqual(
                prediction["model_version"], self.proof_prediction.model_version
            )


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
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["price_count"], 50)


class ProofListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        # type RECEIPT
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session.user.user_id
        )
        # type RECEIPT, but not owned by the user
        ProofFactory(type=proof_constants.TYPE_RECEIPT, price_count=15)
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
        self.assertEqual(response.data["total"], 2)
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.proof.id)
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
            "file": create_fake_image(),  # open("filename.webp", "rb"),
            **PROOF,
            "price_count": 15,
            "source": "test",
        }

    def tearDown(self):
        """Clean delete to remove images"""
        [p.delete() for p in Proof.objects.all()]
        return super().tearDown()

    def test_proof_create(self):
        # anonymous
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["file_path"] is not None)
        self.assertEqual(response.data["owner"], None)
        self.assertEqual(response.data["anonymous"], True)

        # authenticated
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["file_path"] is not None)
        self.assertTrue(response.data["image_thumb_path"] is None)  # .bin
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["price_count"], 0)  # ignored
        self.assertEqual(response.data["owner"], self.user_session.user.user_id)
        self.assertTrue("source" not in response.data)
        self.assertEqual(Proof.objects.last().source, "API")  # default value

    def test_proof_create_with_location_id(self):
        location_osm = LocationFactory(**LOCATION_OSM_NODE_652825274)
        location_online = LocationFactory(type=location_constants.TYPE_ONLINE)
        # with location_id, location_osm_id & location_osm_type: OK
        response = self.client.post(
            self.url,
            {**self.data, "location_id": location_osm.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["location"]["id"], location_osm.id)
        # with just location_id (OSM): NOK
        data = self.data.copy()
        del data["location_osm_id"]
        del data["location_osm_type"]
        response = self.client.post(
            self.url,
            {**data, "location_id": location_osm.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        # with just location_id (ONLINE): OK
        data = self.data.copy()
        del data["location_osm_id"]
        del data["location_osm_type"]
        response = self.client.post(
            self.url,
            {**data, "location_id": location_online.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)

    def test_proof_create_with_app_name(self):
        for params, result in [
            ("?", "API"),
            ("?app_name=", ""),
            ("?app_name=test app&app_version=", "test app"),
            ("?app_name=mobile&app_version=1.0", "mobile (1.0)"),
        ]:
            with self.subTest(INPUT_OUPUT=(params, result)):
                # with empty app_name
                response = self.client.post(
                    self.url + params,
                    self.data,
                    headers={"Authorization": f"Bearer {self.user_session.token}"},
                )
                self.assertEqual(response.status_code, 201)
                self.assertTrue("source" not in response.data)
                self.assertEqual(Proof.objects.last().source, result)


class ProofUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session_1.user.user_id
        )
        cls.url = reverse("api:proofs-detail", args=[cls.proof.id])
        cls.data = {
            "location_osm_id": LOCATION_OSM_NODE_6509705997["osm_id"],
            "location_osm_type": LOCATION_OSM_NODE_6509705997["osm_type"],
            "currency": "USD",
            "receipt_price_count": 4,
            "price_count": 20,
        }

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
        self.assertEqual(
            self.proof.location_osm_id, LOCATION_OSM_NODE_652825274["osm_id"]
        )
        self.assertEqual(self.proof.currency, "EUR")
        self.assertEqual(self.proof.receipt_price_count, 5)
        response = self.client.patch(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session_1.token}"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["location_osm_id"], LOCATION_OSM_NODE_6509705997["osm_id"]
        )
        self.assertEqual(response.data["currency"], "USD")
        self.assertEqual(response.data["receipt_price_count"], 4)
        self.assertEqual(Proof.objects.get(id=self.proof.id).price_count, 15)  # ignored


class ProofDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session_1 = SessionFactory()
        cls.user_session_2 = SessionFactory()
        cls.user_session_3 = SessionFactory()
        cls.moderator = SessionFactory(user__is_moderator=True)
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session_1.user.user_id
        )
        PriceFactory(
            proof_id=cls.proof.id,
            # location_id=cls.proof.location_id,
            location_osm_id=cls.proof.location_osm_id,
            location_osm_type=cls.proof.location_osm_type,
            currency=cls.proof.currency,
            date=cls.proof.date,
            owner=cls.proof.owner,
        )
        proof_2_data = PROOF.copy()
        proof_2_data["date"] = "2024-06-06"
        cls.proof_2 = ProofFactory(
            **proof_2_data, price_count=0, owner=cls.user_session_3.user.user_id
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
        # has prices
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 403)
        # authenticated and no prices
        Price.objects.filter(proof=self.proof).delete()
        response = self.client.delete(
            self.url, headers={"Authorization": f"Bearer {self.user_session_1.token}"}
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertEqual(
            Proof.objects.filter(owner=self.user_session_1.user.user_id).count(), 0
        )

        # Delete request from a moderator, should work
        # Proof 1 was deleted, let's delete proof 2
        url_proof_2 = reverse("api:proofs-detail", args=[self.proof_2.id])
        response = self.client.delete(
            url_proof_2,
            headers={"Authorization": f"Bearer {self.moderator.token}"},
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertEqual(Proof.objects.filter(id=self.proof_2.id).count(), 0)
