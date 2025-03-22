from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import (
    PriceTagFactory,
    ProofFactory,
    ProofPredictionFactory,
)
from open_prices.proofs.models import PriceTag, Proof
from open_prices.users.factories import SessionFactory

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_address_country": "France",
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
        # anonymous
        # thanks to select_related, we only have 2 queries:
        # - 1 to count the number of proofs of the user
        # - 1 to get the proofs and their associated location
        with self.assertNumQueries(2):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            data = response.data
            self.assertEqual(data["total"], 3)
            self.assertEqual(len(data["items"]), 3)
            item = data["items"][0]
            self.assertEqual(item["id"], self.proof.id)  # default order
            self.assertNotIn("predictions", item)  # not returned in "list"


class ProofListOrderApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session.user.user_id
        )
        ProofFactory(type=proof_constants.TYPE_PRICE_TAG, price_count=0)
        ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            price_count=50,
            owner=cls.user_session.user.user_id,
        )

    def test_proof_list_order_by(self):
        url = self.url + "?order_by=-price_count"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["items"][0]["price_count"], 50)


class ProofListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:proofs-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(
            **PROOF, price_count=15, owner=cls.user_session.user.user_id
        )
        ProofFactory(type=proof_constants.TYPE_PRICE_TAG, price_count=0)
        ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            price_count=50,
            owner=cls.user_session.user.user_id,
        )

    def test_proof_list_filter_by_type(self):
        url = self.url + "?type=RECEIPT"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["price_count"], 15)
        url = self.url + "?type=PRICE_TAG"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 2)
        url = self.url + "?type=RECEIPT&type=PRICE_TAG"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1 + 2)

    def test_proof_list_filter_by_owner(self):
        url = self.url + f"?owner={self.user_session.user.user_id}"
        response = self.client.get(url)
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
        cls.proof_prediction = ProofPredictionFactory(
            proof=cls.proof, type="CLASSIFICATION"
        )
        cls.url = reverse("api:proofs-detail", args=[cls.proof.id])

    def test_proof_detail(self):
        # 404
        url = reverse("api:proofs-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "No Proof matches the given query.")
        # anonymous
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.proof.id)
        self.assertIn("predictions", response.data)  # returned in "detail"
        self.assertEqual(len(response.data["predictions"]), 1)
        prediction = response.data["predictions"][0]
        self.assertEqual(prediction["type"], self.proof_prediction.type)
        self.assertEqual(prediction["model_name"], self.proof_prediction.model_name)
        self.assertEqual(
            prediction["model_version"], self.proof_prediction.model_version
        )


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

    def test_proof_create_anonymous(self):
        # wrong endpoint
        response = self.client.post(reverse("api:proofs-list"), self.data)
        self.assertEqual(response.status_code, 403)  # 405 ?
        # anonymous
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["file_path"] is not None)
        self.assertTrue(response.data["image_thumb_path"] is None)  # .bin
        self.assertEqual(response.data["currency"], "EUR")
        self.assertEqual(response.data["price_count"], 0)  # ignored
        self.assertEqual(response.data["owner"], settings.ANONYMOUS_USER_ID)
        self.assertEqual(Proof.objects.last().source, "API")  # default value
        # wrong token
        response = self.client.post(
            self.url,
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}X"},
        )
        self.assertEqual(response.status_code, 201)  # 403 ?
        self.assertEqual(response.data["owner"], settings.ANONYMOUS_USER_ID)

    def test_proof_create_authenticated(self):
        # wrong endpoint
        response = self.client.post(
            reverse("api:proofs-list"),
            self.data,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 405)
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
            (
                "?app_name=web&app_version=&app_page=/prices/add/multiple",
                "web - /prices/add/multiple",
            ),
        ]:
            with self.subTest(INPUT_OUPUT=(params, result)):
                # with empty app_name
                response = self.client.post(
                    self.url + params,
                    self.data,
                    headers={"Authorization": f"Bearer {self.user_session.token}"},
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.data["source"], result)
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


class PriceTagListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:price-tags-list")
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.proof_2 = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price = PriceFactory(proof=cls.proof)
        cls.price_tag_1 = PriceTagFactory(
            proof=cls.proof,
            price=cls.price,
            status=proof_constants.PriceTagStatus.linked_to_price.value,
        )
        cls.price_tag_2 = PriceTagFactory(proof=cls.proof)
        cls.price_tag_3 = PriceTagFactory(
            proof=cls.proof_2, status=proof_constants.PriceTagStatus.deleted
        )

    def test_price_tag_list(self):
        # Check that we can access price tags anonymously
        # We only have 3 queries:
        # - 1 to count the number of price tags
        # - 1 to get the price tags and their associated proof
        # - 1 to get the price tag predictions (prefetch related)
        with self.assertNumQueries(3):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            data = response.data

        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)
        item = data["items"][0]
        self.assertEqual(item["id"], self.price_tag_1.id)  # default order: created
        self.assertNotIn("price", item)  # not returned in "list"
        self.assertEqual(item["price_id"], self.price.id)
        item_2 = data["items"][1]
        self.assertEqual(item_2["id"], self.price_tag_2.id)
        self.assertIsNone(item_2["price_id"])

    def test_price_tag_list_filter_with_status(self):
        url = self.url + "?status=0"  # deleted
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["id"], self.price_tag_3.id)

    def test_price_tag_list_filter_with_status_is_null(self):
        url = self.url + "?status__isnull=True"
        response = self.client.get(url)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["items"]), 1)
        # Price tag 1 is linked to price, price tag 3 is deleted, so only
        # price tag 2 is returned
        self.assertEqual(response.data["items"][0]["id"], self.price_tag_2.id)


class PriceTagDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price = PriceFactory(proof=cls.proof)
        cls.price_tag_1 = PriceTagFactory(proof=cls.proof)
        cls.price_tag_2 = PriceTagFactory(proof=cls.proof, price=cls.price)
        cls.url = reverse("api:price-tags-detail", args=[cls.price_tag_2.id])

    def test_price_tag_detail(self):
        # Check that we can retrieve a single price tags anonymously
        with self.assertNumQueries(2):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["id"], self.price_tag_2.id)
        self.assertIn("proof", data.keys())
        proof = data["proof"]
        self.assertEquals(proof["id"], self.proof.id)
        self.assertEqual(proof["type"], proof_constants.TYPE_PRICE_TAG)
        self.assertNotIn("price", data)  # not returned in "detail"
        self.assertEqual(data["price_id"], self.price.id)


class PriceTagCreateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("api:price-tags-list")
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price = PriceFactory(proof=cls.proof)
        cls.default_bounding_box = [0.1, 0.2, 0.3, 0.4]

    def test_price_tag_create_unauthenticated(self):
        response = self.client.post(
            self.url,
            data={"bounding_box": self.default_bounding_box, "proof_id": self.proof.id},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {"detail": "Authentication credentials were not provided."}
        )

    def test_price_tag_create_missing_proof_id(self):
        response = self.client.post(
            self.url,
            data={"bounding_box": self.default_bounding_box},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.data, {"proof_id": ["This field is required."]})

    def test_price_tag_create_proof_not_found(self):
        response = self.client.post(
            self.url,
            data={"bounding_box": self.default_bounding_box, "proof_id": 999},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.data, {"proof_id": ['Invalid pk "999" - object does not exist.']}
        )

    def test_price_tag_create_price_not_found(self):
        response = self.client.post(
            self.url,
            data={
                "bounding_box": self.default_bounding_box,
                "proof_id": self.proof.id,
                "price_id": 998,
            },
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.data, {"price_id": ['Invalid pk "998" - object does not exist.']}
        )

    def test_price_tag_create(self):
        response = self.client.post(
            self.url,
            data={"bounding_box": self.default_bounding_box, "proof_id": self.proof.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created_by"], self.user_session.user.user_id)
        self.assertEqual(response.data["updated_by"], self.user_session.user.user_id)
        self.assertEqual(response.data["status"], None)
        self.assertEqual(response.data["bounding_box"], self.default_bounding_box)
        self.assertEqual(response.data["price_id"], None)

    def test_price_tag_create_with_price(self):
        response = self.client.post(
            self.url,
            data={
                "bounding_box": self.default_bounding_box,
                "proof_id": self.proof.id,
                "price_id": self.price.id,
            },
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created_by"], self.user_session.user.user_id)
        self.assertEqual(response.data["updated_by"], self.user_session.user.user_id)
        self.assertEqual(response.data["price_id"], self.price.id)
        self.assertEqual(
            response.data["status"],
            proof_constants.PriceTagStatus.linked_to_price.value,
        )


class PriceTagUpdateApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.proof_2 = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price = PriceFactory(proof=cls.proof)
        cls.price_2 = PriceFactory(proof=cls.proof_2)
        cls.price_tag = PriceTagFactory(proof=cls.proof)
        cls.url = reverse("api:price-tags-detail", args=[cls.price_tag.id])
        cls.new_bounding_box = [0.2, 0.3, 0.4, 0.5]

    def test_price_tag_create_unauthenticated(self):
        response = self.client.patch(
            self.url, data={"bounding_box": self.new_bounding_box}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {"detail": "Authentication credentials were not provided."}
        )

    def test_price_tag_create_update_read_only_fields(self):
        self.assertNotEqual(self.price_tag.bounding_box, self.new_bounding_box)
        response = self.client.patch(
            self.url,
            content_type="application/json",
            data={
                "bounding_box": self.new_bounding_box,
                "proof_id": self.proof_2.id,
            },
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        # Proof ID didn't change
        self.assertEqual(response.data["proof"]["id"], self.proof.id)
        # New bounding box was set
        self.assertEqual(response.data["bounding_box"], self.new_bounding_box)

    def test_price_tag_set_price_id(self):
        self.assertEqual(self.price_tag.price_id, None)
        self.assertEqual(self.price_tag.status, None)
        response = self.client.patch(
            self.url,
            content_type="application/json",
            data={"price_id": self.price.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        # Price ID was set to the new value
        self.assertEqual(response.data["price_id"], self.price.id)
        # Status was automatically set to linked_to_price
        self.assertEqual(
            response.data["status"],
            proof_constants.PriceTagStatus.linked_to_price.value,
        )

    def test_price_tag_set_invalid_price_id(self):
        self.assertEqual(self.price_tag.price_id, None)
        response = self.client.patch(
            self.url,
            content_type="application/json",
            # Price associated with another proof
            data={"price_id": self.price_2.id},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"price": ["Price should belong to the same proof."]}
        )

    def test_price_tag_set_status(self):
        self.assertEqual(self.price_tag.status, None)
        response = self.client.patch(
            self.url,
            content_type="application/json",
            # Price associated with another proof
            data={"status": proof_constants.PriceTagStatus.not_readable.value},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"], proof_constants.PriceTagStatus.not_readable.value
        )

    def test_price_tag_invalid_status(self):
        self.assertEqual(self.price_tag.status, None)
        response = self.client.patch(
            self.url,
            content_type="application/json",
            # Invalid status value
            data={"status": 999},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"status": ['"999" is not a valid choice.']})

    def test_price_tag_set_new_bounding_box(self):
        self.assertNotEqual(self.price_tag.bounding_box, self.new_bounding_box)
        response = self.client.patch(
            self.url,
            content_type="application/json",
            data={"bounding_box": self.new_bounding_box},
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["bounding_box"], self.new_bounding_box)

    def test_price_tag_invalid_bounding_box(self):
        response = self.client.patch(
            self.url,
            content_type="application/json",
            data={"bounding_box": [0.1, 0.2, 0.3]},  # only 3 values
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"bounding_box": ["Bounding box should have 4 values."]}
        )


class PriceTagDeleteApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_session = SessionFactory()
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price = PriceFactory(proof=cls.proof)
        cls.price_tag = PriceTagFactory(proof=cls.proof)
        cls.price_tag_with_associated_price = PriceTagFactory(
            proof=cls.proof, price=cls.price
        )
        cls.url = reverse("api:price-tags-detail", args=[cls.price_tag.id])
        cls.url_with_associated_price = reverse(
            "api:price-tags-detail", args=[cls.price_tag_with_associated_price.id]
        )

    def test_price_tag_delete_unauthenticated(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {"detail": "Authentication credentials were not provided."}
        )

    def test_price_tag_delete_with_associated_price(self):
        response = self.client.delete(
            self.url_with_associated_price,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data, {"detail": "Cannot delete price tag with associated prices."}
        )

    def test_price_tag_delete(self):
        response = self.client.delete(
            self.url,
            headers={"Authorization": f"Bearer {self.user_session.token}"},
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertEqual(PriceTag.objects.filter(id=self.price_tag.id).count(), 1)
        self.assertEqual(
            PriceTag.objects.get(id=self.price_tag.id).status,
            proof_constants.PriceTagStatus.deleted,
        )
