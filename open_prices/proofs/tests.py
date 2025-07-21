import gzip
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import numpy as np
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from PIL import Image

from open_prices.challenges.factories import ChallengeFactory
from open_prices.common import constants
from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices import constants as price_constants
from open_prices.prices.factories import PriceFactory
from open_prices.prices.models import Price
from open_prices.products.factories import ProductFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import (
    PriceTagFactory,
    ProofFactory,
    ProofPredictionFactory,
    ReceiptItemFactory,
)
from open_prices.proofs.ml import (
    PRICE_TAG_DETECTOR_MODEL_NAME,
    PRICE_TAG_DETECTOR_MODEL_VERSION,
    PROOF_CLASSIFICATION_MODEL_NAME,
    PROOF_CLASSIFICATION_MODEL_VERSION,
    ObjectDetectionRawResult,
    create_price_tags_from_proof_prediction,
    fetch_and_save_ocr_data,
    run_and_save_price_tag_detection,
    run_and_save_proof_prediction,
    run_and_save_proof_type_prediction,
)
from open_prices.proofs.models import PriceTag, PriceTagPrediction, Proof, ReceiptItem
from open_prices.proofs.utils import (
    match_category_price_tag_with_category_price,
    match_price_tag_with_price,
    match_product_price_tag_with_product_price,
    match_receipt_item_with_price,
    select_proof_image_dir,
)

PRODUCT_8001505005707 = {
    "code": "8001505005707",
    "product_name": "Nocciolata",
    "categories_tags": ["en:breakfasts", "en:spreads"],
    "labels_tags": ["en:no-gluten", "en:organic"],
    "brands_tags": ["rigoni-di-asiago"],
    "price_count": 15,
}

PRODUCT_8850187002197 = {
    "code": "8850187002197",
    "product_name": "Riz 20 kg",
    "categories_tags": ["en:rices"],
    "labels_tags": [],
    "brands_tags": ["royal-umbrella"],
    "price_count": 10,
}

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
    "osm_address_country": "France",
}
LOCATION_OSM_NODE_6509705997 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 6509705997,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Carrefour",
}


class ProofQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_without_price_1 = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG, source="Open Prices Web App"
        )
        PriceTagFactory(proof=cls.proof_without_price_1)
        cls.proof_without_price_2 = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, source="Open Prices Web App"
        )
        ReceiptItemFactory(proof=cls.proof_without_price_2)
        cls.proof_without_price_3 = ProofFactory(
            type=proof_constants.TYPE_RECEIPT,
            owner_consumption=True,
            source="Open Prices Web App",
        )
        cls.proof_with_price = ProofFactory(
            type=proof_constants.TYPE_GDPR_REQUEST,
            owner_consumption=True,
            tags=["challenge-1"],
        )
        PriceFactory(proof_id=cls.proof_with_price.id, price=1.0)

    def test_has_type_group_single_shop(self):
        self.assertEqual(Proof.objects.count(), 4)
        self.assertEqual(Proof.objects.has_type_group_single_shop().count(), 3)

    def test_has_kind_community(self):
        self.assertEqual(Proof.objects.count(), 4)
        self.assertEqual(Proof.objects.has_kind_community().count(), 1)

    def test_has_kind_consumption(self):
        self.assertEqual(Proof.objects.count(), 4)
        self.assertEqual(Proof.objects.has_kind_consumption().count(), 3)

    def test_has_prices(self):
        self.assertEqual(Proof.objects.count(), 4)
        self.assertEqual(Proof.objects.has_prices().count(), 1)

    def with_extra_fields(self):
        self.assertEqual(Proof.objects.count(), 4)
        self.assertEqual(Proof.objects.with_extra_fields().count(), 4)
        self.assertEqual(
            Proof.objects.with_extra_fields()
            .filter(kind_annotated=constants.KIND_COMMUNITY)
            .count(),
            2,
        )
        self.assertEqual(
            Proof.objects.with_extra_fields()
            .filter(source_annotated=constants.SOURCE_WEB)
            .count(),
            2,
        )

    def test_with_stats(self):
        proof = Proof.objects.with_stats().get(id=self.proof_without_price_1.id)
        self.assertEqual(proof.price_count_annotated, 0)
        self.assertEqual(proof.price_count, 0)
        self.assertEqual(proof.price_tag_count_annotated, 1)
        self.assertEqual(proof.receipt_item_count_annotated, 0)
        proof = Proof.objects.with_stats().get(id=self.proof_without_price_2.id)
        self.assertEqual(proof.price_count_annotated, 0)
        self.assertEqual(proof.price_count, 0)
        self.assertEqual(proof.price_tag_count_annotated, 0)
        self.assertEqual(proof.receipt_item_count_annotated, 1)
        proof = Proof.objects.with_stats().get(id=self.proof_with_price.id)
        self.assertEqual(proof.price_count_annotated, 1)
        self.assertEqual(proof.price_count, 1)
        self.assertEqual(proof.price_tag_count_annotated, 0)
        self.assertEqual(proof.receipt_item_count_annotated, 0)

    def test_has_tag(self):
        self.assertEqual(Proof.objects.count(), 4)
        self.assertEqual(Proof.objects.has_tag("challenge-1").count(), 1)
        self.assertEqual(Proof.objects.has_tag("unknown").count(), 0)


class ProofChallengeQuerySetAndPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.challenge_ongoing = ChallengeFactory(
            is_published=True,
            start_date="2024-12-30",
            end_date="2025-01-30",
            categories=["en:breakfasts"],
        )
        cls.proof_in_challenge = ProofFactory()
        cls.proof_not_in_challenge = ProofFactory()
        cls.product_8001505005707 = ProductFactory(
            **PRODUCT_8001505005707
        )  # in challenge
        cls.product_8850187002197 = ProductFactory(**PRODUCT_8850187002197)
        with freeze_time("2025-01-01"):  # during the challenge
            PriceFactory(proof=cls.proof_not_in_challenge)
            PriceFactory(
                product_code="8001505005707",
                product=cls.product_8001505005707,
                proof=cls.proof_in_challenge,
            )
            PriceFactory(
                product_code="8850187002197", product=cls.product_8850187002197
            )

    def test_in_challenge_queryset(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.in_challenge(self.challenge_ongoing).count(), 1)

    def test_in_challenge_property(self):
        self.assertEqual(
            self.proof_in_challenge.in_challenge(self.challenge_ongoing), True
        )
        self.assertEqual(
            self.proof_not_in_challenge.in_challenge(self.challenge_ongoing), False
        )

    def test_on_price_create_signal(self):
        self.proof_in_challenge.refresh_from_db()
        self.proof_not_in_challenge.refresh_from_db()
        self.assertIn(
            f"challenge-{self.challenge_ongoing.id}", self.proof_in_challenge.tags
        )
        self.assertNotIn(
            f"challenge-{self.challenge_ongoing.id}", self.proof_not_in_challenge.tags
        )


class ProofModelSaveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_proof_date_validation(self):
        for DATE_OK in [None, "2024-01-01"]:
            ProofFactory(date=DATE_OK)
        for DATE_NOT_OK in ["3000-01-01", "01-01-2000"]:
            self.assertRaises(ValidationError, ProofFactory, date=DATE_NOT_OK)

    def test_proof_location_validation(self):
        location_osm = LocationFactory()
        location_online = LocationFactory(type=location_constants.TYPE_ONLINE)
        # both location_osm_id & location_osm_type not set
        ProofFactory(location_osm_id=None, location_osm_type=None)
        # location_osm_id
        for LOCATION_OSM_ID_OK in location_constants.OSM_ID_OK_LIST:
            ProofFactory(
                location_osm_id=LOCATION_OSM_ID_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        for LOCATION_OSM_ID_NOT_OK in location_constants.OSM_ID_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=LOCATION_OSM_ID_NOT_OK,
                location_osm_type=location_constants.OSM_TYPE_NODE,
            )
        # location_osm_type
        for LOCATION_OSM_TYPE_OK in location_constants.OSM_TYPE_OK_LIST:
            ProofFactory(
                location_osm_id=652825274, location_osm_type=LOCATION_OSM_TYPE_OK
            )
        for LOCATION_OSM_TYPE_NOT_OK in location_constants.OSM_TYPE_NOT_OK_LIST:
            self.assertRaises(
                ValidationError,
                ProofFactory,
                location_osm_id=652825274,
                location_osm_type=LOCATION_OSM_TYPE_NOT_OK,
            )
        # location_id unknown
        self.assertRaises(
            ValidationError,
            ProofFactory,
            location_id=999,
            location_osm_id=None,
            location_osm_type=None,
        )
        # cannot mix location_id & location_osm_id/type
        self.assertRaises(
            ValidationError,
            ProofFactory,
            location_id=location_osm.id,
            location_osm_id=None,  # needed
            location_osm_type=None,  # needed
        )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            location_id=location_online.id,
            location_osm_id=LOCATION_OSM_ID_OK,  # should be None
        )
        # location_id ok
        ProofFactory(
            location_id=location_osm.id,
            location_osm_id=location_osm.osm_id,
            location_osm_type=location_osm.osm_type,
        )
        ProofFactory(
            location_id=location_online.id, location_osm_id=None, location_osm_type=None
        )

    def test_proof_price_tag_fields(self):
        # ready_for_price_tag_validation
        self.assertRaises(
            ValidationError,
            ProofFactory,
            ready_for_price_tag_validation=True,
            type=proof_constants.TYPE_RECEIPT,
        )
        ProofFactory(
            ready_for_price_tag_validation=True,
            type=proof_constants.TYPE_PRICE_TAG,
        )

    def test_proof_receipt_fields(self):
        # receipt_price_count
        for RECEIPT_PRICE_COUNT_NOT_OK in [-5]:  # Decimal("45.10")
            with self.subTest(RECEIPT_PRICE_COUNT_NOT_OK=RECEIPT_PRICE_COUNT_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    ProofFactory,
                    receipt_price_count=RECEIPT_PRICE_COUNT_NOT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        for RECEIPT_PRICE_COUNT_OK in [None, 0, 5]:
            with self.subTest(RECEIPT_PRICE_COUNT_OK=RECEIPT_PRICE_COUNT_OK):
                ProofFactory(
                    receipt_price_count=RECEIPT_PRICE_COUNT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            receipt_price_count=5,
            type=proof_constants.TYPE_PRICE_TAG,
        )
        # receipt_price_total
        for RECEIPT_PRICE_TOTAL_NOT_OK in [-5]:
            with self.subTest(RECEIPT_PRICE_TOTAL_NOT_OK=RECEIPT_PRICE_TOTAL_NOT_OK):
                self.assertRaises(
                    ValidationError,
                    ProofFactory,
                    receipt_price_total=RECEIPT_PRICE_TOTAL_NOT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        for RECEIPT_PRICE_TOTAL_OK in [None, 0, 5, Decimal("45.10")]:
            with self.subTest(RECEIPT_PRICE_TOTAL_OK=RECEIPT_PRICE_TOTAL_OK):
                ProofFactory(
                    receipt_price_total=RECEIPT_PRICE_TOTAL_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            receipt_price_total=5,
            type=proof_constants.TYPE_PRICE_TAG,
        )
        # receipt_online_delivery_costs
        for RECEIPT_ONLINE_DELIVERY_COSTS_NOT_OK in [-5]:
            with self.subTest(
                RECEIPT_ONLINE_DELIVERY_COSTS_NOT_OK=RECEIPT_ONLINE_DELIVERY_COSTS_NOT_OK
            ):
                self.assertRaises(
                    ValidationError,
                    ProofFactory,
                    receipt_online_delivery_costs=RECEIPT_ONLINE_DELIVERY_COSTS_NOT_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        for RECEIPT_ONLINE_DELIVERY_COSTS_OK in [None, 0, 5, Decimal("45.10")]:
            with self.subTest(
                RECEIPT_ONLINE_DELIVERY_COSTS_OK=RECEIPT_ONLINE_DELIVERY_COSTS_OK
            ):
                ProofFactory(
                    receipt_online_delivery_costs=RECEIPT_ONLINE_DELIVERY_COSTS_OK,
                    type=proof_constants.TYPE_RECEIPT,
                )
        self.assertRaises(
            ValidationError,
            ProofFactory,
            receipt_online_delivery_costs=5,
            type=proof_constants.TYPE_PRICE_TAG,
        )

    def test_proof_owner_fields(self):
        # owner_consumption: can be set only for consumption-type proofs
        for OWNER_CONSUMPTION_OK in [None, True, False]:
            for PROOF_TYPE in proof_constants.TYPE_GROUP_CONSUMPTION_LIST:
                with self.subTest(OWNER_CONSUMPTION_OK=OWNER_CONSUMPTION_OK):
                    ProofFactory(
                        type=PROOF_TYPE,
                        owner_consumption=OWNER_CONSUMPTION_OK,
                    )
        for OWNER_CONSUMPTION_NOT_OK in [True, False]:
            for PROOF_TYPE in proof_constants.TYPE_GROUP_COMMUNITY_LIST:
                with self.subTest(OWNER_CONSUMPTION_NOT_OK=OWNER_CONSUMPTION_NOT_OK):
                    self.assertRaises(
                        ValidationError,
                        ProofFactory,
                        type=PROOF_TYPE,
                        owner_consumption=OWNER_CONSUMPTION_NOT_OK,
                    )
        # owner_comment
        for OWNER_COMMENT_OK in [None, "", "test"]:
            ProofFactory(owner_comment=OWNER_COMMENT_OK)


class ProofPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_osm_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_osm_2 = LocationFactory(**LOCATION_OSM_NODE_6509705997)
        cls.proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location_osm_1.osm_id,
            location_osm_type=cls.location_osm_1.osm_type,
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.proof_price_tag.location.osm_id,
            location_osm_type=cls.proof_price_tag.location.osm_type,
            price=1.0,
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.proof_price_tag.location.osm_id,
            location_osm_type=cls.proof_price_tag.location.osm_type,
            price=2.0,
        )
        cls.proof_receipt = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, owner_consumption=True
        )
        PriceFactory(
            proof_id=cls.proof_receipt.id,
            location_osm_id=cls.location_osm_1.osm_id,
            location_osm_type=cls.location_osm_1.osm_type,
            price=2.0,
            currency="EUR",
            date="2024-06-30",
        )

    def test_is_type_single_shop(self):
        self.assertTrue(self.proof_price_tag.is_type_single_shop)

    def test_kind(self):
        self.assertEqual(self.proof_price_tag.kind, constants.KIND_COMMUNITY)
        self.assertEqual(self.proof_receipt.kind, constants.KIND_CONSUMPTION)

    def test_update_price_count(self):
        self.proof_price_tag.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)  # price post_save
        # bulk delete prices to skip signals
        self.proof_price_tag.prices.all().delete()
        self.assertEqual(self.proof_price_tag.price_count, 2)  # should be 0
        # update_price_count() should fix price_count
        self.proof_price_tag.update_price_count()
        self.assertEqual(self.proof_price_tag.price_count, 0)  # all deleted

    def test_update_location(self):
        # existing
        self.proof_price_tag.refresh_from_db()
        self.location_osm_1.refresh_from_db()
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(self.proof_price_tag.location.id, self.location_osm_1.id)
        self.assertEqual(self.location_osm_1.price_count, 2 + 1)
        # update location
        self.proof_price_tag.update_location(
            location_osm_id=self.location_osm_2.osm_id,
            location_osm_type=self.location_osm_2.osm_type,
        )
        # check changes
        self.proof_price_tag.refresh_from_db()
        self.location_osm_1.refresh_from_db()
        self.location_osm_2.refresh_from_db()
        self.assertEqual(self.proof_price_tag.location, self.location_osm_2)
        self.assertEqual(self.proof_price_tag.price_count, 2)  # same
        self.assertEqual(self.proof_price_tag.location.price_count, 2)
        self.assertEqual(self.location_osm_1.price_count, 3 - 2)
        self.assertEqual(self.location_osm_2.price_count, 2)
        # update again, same location
        self.proof_price_tag.update_location(
            location_osm_id=self.location_osm_2.osm_id,
            location_osm_type=self.location_osm_2.osm_type,
        )
        self.proof_price_tag.refresh_from_db()
        self.location_osm_1.refresh_from_db()
        self.location_osm_2.refresh_from_db()
        self.assertEqual(self.proof_price_tag.location, self.location_osm_2)
        self.assertEqual(self.proof_price_tag.price_count, 2)
        self.assertEqual(self.proof_price_tag.location.price_count, 2)
        self.assertEqual(self.location_osm_1.price_count, 1)
        self.assertEqual(self.location_osm_2.price_count, 2)

    def test_set_missing_fields_from_prices(self):
        self.proof_receipt.refresh_from_db()
        self.assertTrue(self.proof_receipt.location is None)
        self.assertTrue(self.proof_receipt.date is None)
        self.assertTrue(self.proof_receipt.currency is None)
        self.assertEqual(self.proof_receipt.price_count, 1)
        self.proof_receipt.set_missing_fields_from_prices()
        self.assertEqual(self.proof_receipt.location, self.location_osm_1)
        self.assertEqual(
            self.proof_receipt.date, self.proof_receipt.prices.first().date
        )
        self.assertEqual(
            self.proof_receipt.currency, self.proof_receipt.prices.first().currency
        )


class ProofModelUpdateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.location_osm_1 = LocationFactory(**LOCATION_OSM_NODE_652825274)
        cls.location_osm_2 = LocationFactory(**LOCATION_OSM_NODE_6509705997)
        cls.proof_price_tag = ProofFactory(
            type=proof_constants.TYPE_PRICE_TAG,
            location_osm_id=cls.location_osm_1.osm_id,
            location_osm_type=cls.location_osm_1.osm_type,
            currency="EUR",
            date="2024-06-30",
        )
        PriceFactory(
            proof_id=cls.proof_price_tag.id,
            location_osm_id=cls.proof_price_tag.location.osm_id,
            location_osm_type=cls.proof_price_tag.location.osm_type,
            price=1.0,
            currency="EUR",
            date="2024-06-30",
        )

    def test_proof_update(self):
        # currency
        self.assertEqual(self.proof_price_tag.prices.count(), 1)
        self.proof_price_tag.currency = "USD"
        self.proof_price_tag.save()
        self.assertEqual(self.proof_price_tag.prices.first().currency, "USD")
        # date
        self.proof_price_tag.date = "2024-07-01"
        self.proof_price_tag.save()
        self.assertEqual(str(self.proof_price_tag.prices.first().date), "2024-07-01")
        # location
        self.proof_price_tag.location_osm_id = self.location_osm_2.osm_id
        self.proof_price_tag.location_osm_type = self.location_osm_2.osm_type
        self.proof_price_tag.save()
        self.proof_price_tag.refresh_from_db()
        self.assertEqual(self.proof_price_tag.location, self.location_osm_2)
        self.assertEqual(
            self.proof_price_tag.prices.first().location, self.location_osm_2
        )


class RunOCRTaskTest(TestCase):
    def test_fetch_and_save_ocr_data_success(self):
        response_data = {"responses": [{"textAnnotations": [{"description": "test"}]}]}
        with self.settings(GOOGLE_CLOUD_VISION_API_KEY="test_api_key"):
            # mock call to run_ocr_on_image
            with unittest.mock.patch(
                "open_prices.proofs.ml.run_ocr_on_image",
                return_value=response_data,
            ) as mock_run_ocr_on_image:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    image_path = Path(f"{tmpdirname}/test.jpg")
                    with image_path.open("w") as f:
                        f.write("test")
                    output = fetch_and_save_ocr_data(image_path)
                    self.assertTrue(output)
                    mock_run_ocr_on_image.assert_called_once_with(
                        image_path, "test_api_key"
                    )
                    ocr_path = image_path.with_suffix(".json.gz")
                    self.assertTrue(ocr_path.is_file())

                    with gzip.open(ocr_path, "rt") as f:
                        actual_data = json.loads(f.read())
                        self.assertEqual(
                            set(actual_data.keys()), {"responses", "created_at"}
                        )
                        self.assertIsInstance(actual_data["created_at"], int)
                        self.assertEqual(
                            actual_data["responses"], response_data["responses"]
                        )

    def test_fetch_and_save_ocr_data_invalid_extension(self):
        with self.settings(GOOGLE_CLOUD_VISION_API_KEY="test_api_key"):
            with tempfile.TemporaryDirectory() as tmpdirname:
                image_path = Path(f"{tmpdirname}/test.bin")
                with image_path.open("w") as f:
                    f.write("test")
                output = fetch_and_save_ocr_data(image_path)
                self.assertFalse(output)


class MLModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a white blank image with Pillow
        cls.image = Image.new("RGB", (100, 100), "white")

    def test_run_and_save_proof_prediction_proof_file_not_found(self):
        proof = ProofFactory()
        # check that we emit an error log
        with self.assertLogs("open_prices.proofs.ml", level="ERROR") as cm:
            self.assertIsNone(run_and_save_proof_prediction(proof))
            self.assertEqual(
                cm.output,
                [
                    f"ERROR:open_prices.proofs.ml:Proof file not found: {proof.file_path_full}"
                ],
            )

    def test_run_and_save_proof_prediction_for_receipt_proof(self):
        predict_proof_type_response = [
            ("RECEIPT", 0.9786477088928223),
            ("PRICE_TAG", 0.021345501765608788),
        ]

        # We save the image to a temporary file
        with tempfile.TemporaryDirectory() as tmpdirname:
            NEW_IMAGE_DIR = Path(tmpdirname)
            file_path = NEW_IMAGE_DIR / "1.jpg"
            self.image.save(file_path)

            # change temporarily settings.IMAGE_DIR
            with self.settings(IMAGE_DIR=NEW_IMAGE_DIR):
                proof = ProofFactory(
                    file_path=file_path, type=proof_constants.TYPE_RECEIPT
                )

                # Patch predict_proof_type to return a fixed response
                with (
                    unittest.mock.patch(
                        "open_prices.proofs.ml.predict_proof_type",
                        return_value=predict_proof_type_response,
                    ) as mock_predict_proof_type,
                    unittest.mock.patch(
                        "open_prices.proofs.ml.detect_price_tags",
                        return_value=None,
                    ) as mock_detect_price_tags,
                ):
                    run_and_save_proof_prediction(
                        proof,
                        run_price_tag_extraction=False,
                        run_receipt_extraction=False,
                    )
                    mock_predict_proof_type.assert_called_once()
                    mock_detect_price_tags.assert_not_called()

                proof_type_prediction = proof.predictions.filter(
                    type=proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE
                ).first()
                self.assertIsNotNone(proof_type_prediction)
                self.assertEqual(
                    proof_type_prediction.type,
                    proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
                )

                self.assertEqual(
                    proof_type_prediction.model_name, "price_proof_classification"
                )
                self.assertEqual(
                    proof_type_prediction.model_version,
                    "price_proof_classification-1.0",
                )
                self.assertEqual(proof_type_prediction.value, "RECEIPT")
                self.assertEqual(
                    proof_type_prediction.max_confidence, 0.9786477088928223
                )
                self.assertEqual(
                    proof_type_prediction.data,
                    {
                        "prediction": [
                            {"label": "RECEIPT", "score": 0.9786477088928223},
                            {"label": "PRICE_TAG", "score": 0.021345501765608788},
                        ]
                    },
                )

                price_tag_prediction = proof.predictions.filter(
                    type=proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE
                ).first()
                self.assertIsNone(price_tag_prediction)

                # prediction_count was incremented
                proof.refresh_from_db()
                self.assertEqual(proof.prediction_count, 1)

                # cleanup
                proof_type_prediction.delete()
                proof.delete()

    def test_run_and_save_proof_prediction_for_price_tag_proof(self):
        predict_proof_type_response = [
            ("SHELF", 0.9786477088928223),
            ("PRICE_TAG", 0.021345501765608788),
        ]
        detect_price_tags_response = ObjectDetectionRawResult(
            num_detections=1,
            detection_boxes=np.array([[0.5, 0.5, 1.0, 1.0]]),
            detection_classes=np.array([0], dtype=int),
            detection_scores=np.array([0.98], dtype=np.float32),
            label_names=["price-tag"],
        )

        # We save the image to a temporary file
        with tempfile.TemporaryDirectory() as tmpdirname:
            NEW_IMAGE_DIR = Path(tmpdirname)
            file_path = NEW_IMAGE_DIR / "1.jpg"
            self.image.save(file_path)

            # change temporarily settings.IMAGE_DIR
            with self.settings(IMAGE_DIR=NEW_IMAGE_DIR):
                proof = ProofFactory(
                    file_path=file_path, type=proof_constants.TYPE_PRICE_TAG
                )

                # Patch predict_proof_type to return a fixed response
                with (
                    unittest.mock.patch(
                        "open_prices.proofs.ml.predict_proof_type",
                        return_value=predict_proof_type_response,
                    ) as mock_predict_proof_type,
                    unittest.mock.patch(
                        "open_prices.proofs.ml.detect_price_tags",
                        return_value=detect_price_tags_response,
                    ) as mock_detect_price_tags,
                ):
                    run_and_save_proof_prediction(
                        proof,
                        run_price_tag_extraction=False,
                        run_receipt_extraction=False,
                    )
                    mock_predict_proof_type.assert_called_once()
                    mock_detect_price_tags.assert_called_once()

                proof_type_prediction = proof.predictions.filter(
                    type=proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE
                ).first()
                self.assertIsNotNone(proof_type_prediction)
                self.assertEqual(
                    proof_type_prediction.type,
                    proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
                )

                self.assertEqual(
                    proof_type_prediction.model_name, "price_proof_classification"
                )
                self.assertEqual(
                    proof_type_prediction.model_version,
                    "price_proof_classification-1.0",
                )
                self.assertEqual(proof_type_prediction.value, "SHELF")
                self.assertEqual(
                    proof_type_prediction.max_confidence, 0.9786477088928223
                )
                self.assertEqual(
                    proof_type_prediction.data,
                    {
                        "prediction": [
                            {"label": "SHELF", "score": 0.9786477088928223},
                            {"label": "PRICE_TAG", "score": 0.021345501765608788},
                        ]
                    },
                )

                price_tag_prediction = proof.predictions.filter(
                    type=proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE
                ).first()
                self.assertIsNotNone(price_tag_prediction)
                self.assertEqual(
                    price_tag_prediction.type,
                    proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
                )
                self.assertEqual(price_tag_prediction.model_name, "price_tag_detection")
                self.assertEqual(
                    price_tag_prediction.model_version, "price_tag_detection-1.0"
                )
                self.assertIsNone(price_tag_prediction.value)
                self.assertAlmostEqual(price_tag_prediction.max_confidence, 0.98)
                self.assertIn("objects", price_tag_prediction.data)
                objects = price_tag_prediction.data["objects"]
                self.assertEqual(len(objects), 1)
                self.assertEqual(objects[0]["label"], "price-tag")
                self.assertAlmostEqual(objects[0]["score"], 0.98)
                self.assertEqual(objects[0]["bounding_box"], [0.5, 0.5, 1.0, 1.0])

                # prediction_count was incremented
                proof.refresh_from_db()
                self.assertEqual(proof.prediction_count, 2)

                # cleanup
                proof_type_prediction.delete()
                price_tag_prediction.delete()
                proof.delete()

    def test_run_and_save_proof_type_prediction_already_exists(self):
        proof = ProofFactory()
        ProofPredictionFactory(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
            model_name=PROOF_CLASSIFICATION_MODEL_NAME,
            model_version=PROOF_CLASSIFICATION_MODEL_VERSION,
        )
        result = run_and_save_proof_type_prediction(self.image, proof)
        self.assertIsNone(result)

    def test_run_and_save_price_tag_detection_already_exists(self):
        proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        ProofPredictionFactory(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
            model_name=PRICE_TAG_DETECTOR_MODEL_NAME,
            model_version=PRICE_TAG_DETECTOR_MODEL_VERSION,
            data={
                "objects": [
                    {
                        "label": "price_tag",
                        "score": 0.98,
                        "bounding_box": [0.5, 0.5, 1.0, 1.0],
                    },
                    {
                        "label": "price_tag",
                        "score": 0.8,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                    },
                ]
            },
        )
        result = run_and_save_price_tag_detection(
            self.image, proof, run_extraction=False
        )
        self.assertIsNone(result)
        price_tags = PriceTag.objects.filter(proof=proof).all()
        self.assertEqual(len(price_tags), 2)
        self.assertEqual(price_tags[0].bounding_box, [0.5, 0.5, 1.0, 1.0])
        self.assertEqual(price_tags[1].bounding_box, [0.1, 0.1, 0.2, 0.2])

    def create_price_tags_from_proof_prediction(self):
        proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        proof_prediction = ProofPredictionFactory(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
            model_name=PRICE_TAG_DETECTOR_MODEL_NAME,
            model_version=PRICE_TAG_DETECTOR_MODEL_VERSION,
            data={
                "objects": [
                    {
                        "label": "price_tag",
                        "score": 0.98,
                        "bounding_box": [0.5, 0.5, 1.0, 1.0],
                    },
                    {
                        "label": "price_tag",
                        "score": 0.45,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                    },
                    {
                        "label": "price_tag",
                        "score": 0.4,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                    },
                ]
            },
        )
        before = timezone.now()
        results = create_price_tags_from_proof_prediction(
            proof, proof_prediction, threshold=0.4, run_extraction=False
        )
        after = timezone.now()
        self.assertEqual(len(results), 2)
        price_tags = PriceTag.objects.filter(proof=proof).all()
        self.assertEqual(len(price_tags), 2)

        price_tag_1 = results[0]
        self.assertEqual(price_tag_1.bounding_box, [0.5, 0.5, 1.0, 1.0])
        self.assertGreater(price_tag_1.created, before)
        self.assertLess(price_tag_1.created, after)
        self.assertGreater(price_tag_1.updated, before)
        self.assertLess(price_tag_1.updated, after)
        self.assertEqual(price_tag_1.status, None)
        self.assertEqual(price_tag_1.created_by, None)
        self.assertEqual(price_tag_1.updated_by, None)
        self.assertEqual(price_tag_1.model_version, PRICE_TAG_DETECTOR_MODEL_VERSION)


class TestSelectProofImageDir(TestCase):
    def test_select_proof_image_dir_no_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            selected_dir = select_proof_image_dir(images_dir)
            self.assertEqual(selected_dir, images_dir / "0001")

    def test_select_proof_image_dir_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            (images_dir / "0001").mkdir()
            selected_dir = select_proof_image_dir(images_dir)
            self.assertEqual(selected_dir, images_dir / "0001")

    def test_select_proof_image_dir_existing_dir_second_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            (images_dir / "0001").mkdir()
            (images_dir / "0002").mkdir()
            selected_dir = select_proof_image_dir(images_dir)
            self.assertEqual(selected_dir, images_dir / "0002")

    def test_select_proof_image_dir_existing_dir_create_new_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = Path(tmpdir) / "images"
            images_dir.mkdir()
            (images_dir / "0001").mkdir()
            (images_dir / "0001" / "0001.jpg").touch()
            selected_dir = select_proof_image_dir(images_dir, max_images_per_dir=1)
            self.assertEqual(selected_dir, images_dir / "0002")


class PriceTagQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price_product = PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="0123456789100",
            price=1.5,
            proof=cls.proof,
            location=cls.proof.location,
            # product_name="NAME",
        )
        cls.price_tag_product = PriceTagFactory(
            bounding_box=[0.1, 0.1, 0.2, 0.2],
            proof=cls.proof,
            price=cls.price_product,
            status=proof_constants.PriceTagStatus.linked_to_price.value,
            tags=["prediction-found-product"],
        )
        PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_product,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={
                "price": 1.5,
                "barcode": "0123456789100",
                "product": "other",
                "product_name": "NAME",
            },
        )
        PriceTagFactory(
            bounding_box=[0.1, 0.1, 0.2, 0.2],
            proof=cls.proof,
        )

    def test_status_unknown(self):
        self.assertEqual(PriceTag.objects.count(), 2)
        self.assertEqual(PriceTag.objects.status_unknown().count(), 1)

    def test_status_linked_to_price(self):
        self.assertEqual(PriceTag.objects.count(), 2)
        self.assertEqual(PriceTag.objects.status_linked_to_price().count(), 1)

    def test_has_price_product_name_empty(self):
        self.assertEqual(PriceTag.objects.count(), 2)
        self.assertEqual(PriceTag.objects.has_price_product_name_empty().count(), 2)
        Price.objects.filter(id=self.price_product.id).update(product_name="NAME")
        self.assertEqual(PriceTag.objects.has_price_product_name_empty().count(), 1)

    def test_has_tag(self):
        self.assertEqual(PriceTag.objects.count(), 2)
        self.assertEqual(
            PriceTag.objects.has_tag("prediction-found-product").count(), 1
        )
        self.assertEqual(PriceTag.objects.has_tag("unknown").count(), 0)


class PriceTagModelTest(TestCase):
    def test_create_price_tag_invalid_bounding_box_length(self):
        with self.assertRaises(ValidationError) as cm:
            PriceTagFactory(
                bounding_box=[0.1, 0.2], proof__type=proof_constants.TYPE_PRICE_TAG
            )
        self.assertEqual(
            str(cm.exception),
            "{'bounding_box': ['Bounding box should have 4 values.']}",
        )

    def test_create_price_tag_invalid_bounding_box_value(self):
        with self.assertRaises(ValidationError) as cm:
            PriceTagFactory(
                bounding_box=None, proof__type=proof_constants.TYPE_PRICE_TAG
            )
        self.assertEqual(
            str(cm.exception),
            "{'bounding_box': ['This field cannot be null.']}",
        )

        with self.assertRaises(ValidationError) as cm:
            PriceTagFactory(
                bounding_box=["st", 0.2, 0.3, 0.4],
                proof__type=proof_constants.TYPE_PRICE_TAG,
            )
        self.assertEqual(
            str(cm.exception),
            "{'bounding_box': ['Bounding box values should be floats.']}",
        )

        with self.assertRaises(ValidationError) as cm:
            PriceTagFactory(
                bounding_box=[0.1, 1.2, 0.3, 0.4],
                proof__type=proof_constants.TYPE_PRICE_TAG,
            )
        self.assertEqual(
            str(cm.exception),
            "{'bounding_box': ['Bounding box values should be between 0 and 1.']}",
        )

        with self.assertRaises(ValidationError) as cm:
            PriceTagFactory(
                bounding_box=[0.5, 0.1, 0.4, 0.4],
                proof__type=proof_constants.TYPE_PRICE_TAG,
            )
        self.assertEqual(
            str(cm.exception),
            "{'bounding_box': ['Bounding box values should be in the format [y_min, x_min, y_max, x_max].']}",
        )

    def test_create_price_tag_invalid_proof_type(self):
        with self.assertRaises(ValidationError) as cm:
            PriceTagFactory(
                bounding_box=[0.1, 0.1, 0.2, 0.2],
                proof__type=proof_constants.TYPE_RECEIPT,
            )
        self.assertEqual(
            str(cm.exception),
            "{'proof': ['Proof should have type PRICE_TAG.']}",
        )

    def test_delete_price_should_update_price_tag(self):
        proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        price_tag = PriceTagFactory(proof=proof)
        price = PriceFactory(proof=proof, location=proof.location)
        price_tag.price_id = price.id
        price_tag.status = proof_constants.PriceTagStatus.linked_to_price.value
        price_tag.save()
        # delete price
        price.delete()
        price_tag.refresh_from_db()
        self.assertIsNone(price_tag.price_id)
        self.assertIsNone(price_tag.status)


class PriceTagPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ProductFactory(**PRODUCT_8001505005707)
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price_tag_product = PriceTagFactory(
            bounding_box=[0.1, 0.1, 0.2, 0.2],
            proof=cls.proof,
        )
        PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_product,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={
                "price": 10,
                "barcode": "8001505005707",
                "product": "other",
                "product_name": "NOCCIOLATA 700G",
            },
        )
        cls.price_tag_category = PriceTagFactory(
            bounding_box=[0.2, 0.2, 0.3, 0.3],
            proof=cls.proof,
        )
        PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_category,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={
                "price": 2.5,
                "barcode": "",
                "product": "en:tomatoes",  # category_tag
                "product_name": "TOMATES",
            },
        )
        cls.price_tag_empty = PriceTagFactory(
            bounding_box=[0.3, 0.3, 0.4, 0.4],
            proof=cls.proof,
        )
        PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_category,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={},
        )

    def test_get_predicted_price(self):
        self.assertEqual(self.price_tag_product.get_predicted_price(), 10)
        self.assertEqual(self.price_tag_category.get_predicted_price(), 2.5)
        self.assertEqual(self.price_tag_empty.get_predicted_price(), None)

    def test_get_predicted_barcode(self):
        self.assertEqual(
            self.price_tag_product.get_predicted_barcode(), "8001505005707"
        )
        self.assertEqual(self.price_tag_category.get_predicted_barcode(), "")
        self.assertEqual(self.price_tag_empty.get_predicted_barcode(), None)

    def test_get_predicted_product(self):
        self.assertEqual(self.price_tag_product.get_predicted_product(), "other")
        self.assertEqual(self.price_tag_category.get_predicted_product(), "en:tomatoes")
        self.assertEqual(self.price_tag_empty.get_predicted_product(), None)

    def test_get_predicted_product_name(self):
        self.assertEqual(
            self.price_tag_product.get_predicted_product_name(),
            "NOCCIOLATA 700G",
        )
        self.assertEqual(
            self.price_tag_category.get_predicted_product_name(), "TOMATES"
        )
        self.assertEqual(self.price_tag_empty.get_predicted_product_name(), None)


class PriceTagPredictionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ProductFactory(**PRODUCT_8001505005707)
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price_tag_product = PriceTagFactory(
            bounding_box=[0.1, 0.1, 0.2, 0.2],
            proof=cls.proof,
        )
        cls.price_tag_product_prediction = PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_product,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={
                "price": 10,
                "barcode": "8001505005707",
                "product": "other",
                "product_name": "NOCCIOLATA 700G",
            },
        )
        cls.price_tag_category = PriceTagFactory(
            bounding_box=[0.2, 0.2, 0.3, 0.3],
            proof=cls.proof,
        )
        cls.price_tag_category_prediction = PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_category,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={
                "price": 2.5,
                "barcode": "",
                "product": "en:tomatoes",  # category_tag
                "product_name": "TOMATES",
            },
        )
        cls.price_tag_empty = PriceTagFactory(
            bounding_box=[0.3, 0.3, 0.4, 0.4],
            proof=cls.proof,
        )
        cls.price_tag_empty_prediction = PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_empty,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={},
        )
        cls.price_tag_without = PriceTagFactory(
            bounding_box=[0.4, 0.4, 0.5, 0.5],
            proof=cls.proof,
        )

    def test_on_create_signal(self):
        # price_tag.prediction_count
        for price_tag in PriceTag.objects.all():  # refresh_from_db
            if price_tag in [self.price_tag_without]:
                self.assertEqual(price_tag.prediction_count, 0)
            else:
                self.assertEqual(price_tag.prediction_count, 1)
        # price_tag.tags
        self.assertIn("prediction-barcode-valid", self.price_tag_product.tags)
        self.assertIn("prediction-product-exists", self.price_tag_product.tags)
        self.assertNotIn("prediction-category-tag-valid", self.price_tag_product.tags)
        self.assertNotIn("prediction-barcode-valid", self.price_tag_category.tags)
        self.assertNotIn("prediction-product-exists", self.price_tag_category.tags)
        self.assertIn("prediction-category-tag-valid", self.price_tag_category.tags)
        self.assertNotIn("prediction-barcode-valid", self.price_tag_empty.tags)
        self.assertNotIn("prediction-product-exists", self.price_tag_empty.tags)
        self.assertNotIn("prediction-category-tag-valid", self.price_tag_empty.tags)
        self.assertNotIn("prediction-barcode-valid", self.price_tag_without.tags)
        self.assertNotIn("prediction-product-exists", self.price_tag_without.tags)
        self.assertNotIn("prediction-category-tag-valid", self.price_tag_without.tags)

    def test_has_predicted_barcode_valid(self):
        self.assertTrue(self.price_tag_product_prediction.has_predicted_barcode_valid())
        self.assertFalse(
            self.price_tag_category_prediction.has_predicted_barcode_valid()
        )
        self.assertFalse(self.price_tag_empty_prediction.has_predicted_barcode_valid())

    def test_has_predicted_product_exists(self):
        self.assertTrue(
            self.price_tag_product_prediction.has_predicted_product_exists()
        )
        self.assertFalse(
            self.price_tag_category_prediction.has_predicted_product_exists()
        )
        self.assertFalse(self.price_tag_empty_prediction.has_predicted_product_exists())

    def test_has_predicted_barcode_valid_and_product_exists(self):
        self.assertTrue(
            self.price_tag_product_prediction.has_predicted_barcode_valid_and_product_exists()
        )
        self.assertFalse(
            self.price_tag_category_prediction.has_predicted_barcode_valid_and_product_exists()
        )
        self.assertFalse(
            self.price_tag_empty_prediction.has_predicted_barcode_valid_and_product_exists()
        )

    def test_has_predicted_category_tag_valid(self):
        self.assertFalse(
            self.price_tag_product_prediction.has_predicted_category_tag_valid()
        )
        self.assertTrue(
            self.price_tag_category_prediction.has_predicted_category_tag_valid()
        )
        self.assertFalse(
            self.price_tag_empty_prediction.has_predicted_category_tag_valid()
        )


class PriceTagMatchingUtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.price_tag_product = PriceTagFactory(
            bounding_box=[0.1, 0.1, 0.2, 0.2],
            proof=cls.proof,
        )
        PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_product,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={"price": 1.5, "barcode": "0123456789100", "product": "other"},
        )
        cls.price_product = PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="0123456789100",
            price=1.5,
            proof=cls.proof,
            location=cls.proof.location,
        )
        cls.price_tag_category = PriceTagFactory(
            bounding_box=[0.2, 0.2, 0.3, 0.3],
            proof=cls.proof,
        )
        PriceTagPrediction.objects.create(
            price_tag=cls.price_tag_category,
            type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
            data={
                "price": 2.5,
                "barcode": "",
                "product": "en:tomatoes",  # category_tag
                "product_name": "TOMATES",
            },
        )
        cls.price_category = PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:tomatoes",
            price=2.5,
            price_per=price_constants.PRICE_PER_KILOGRAM,
            proof=cls.proof,
            location=cls.proof.location,
        )

    def test_match_product_price_tag_with_product_price(self):
        self.assertTrue(
            match_product_price_tag_with_product_price(
                self.price_tag_product, self.price_product
            )
        )
        self.assertFalse(
            match_product_price_tag_with_product_price(
                self.price_tag_product, self.price_category
            )
        )
        self.assertFalse(
            match_product_price_tag_with_product_price(
                self.price_tag_category, self.price_category
            )
        )
        self.assertFalse(
            match_product_price_tag_with_product_price(
                self.price_tag_category, self.price_product
            )
        )

    def test_match_category_price_tag_with_category_price(self):
        self.assertFalse(
            match_category_price_tag_with_category_price(
                self.price_tag_product, self.price_product
            )
        )
        self.assertFalse(
            match_category_price_tag_with_category_price(
                self.price_tag_product, self.price_category
            )
        )
        self.assertTrue(
            match_category_price_tag_with_category_price(
                self.price_tag_category, self.price_category
            )
        )
        self.assertFalse(
            match_category_price_tag_with_category_price(
                self.price_tag_category, self.price_product
            )
        )

    def test_match_price_tag_with_price(self):
        self.assertTrue(
            match_price_tag_with_price(self.price_tag_product, self.price_product)
        )
        self.assertFalse(
            match_price_tag_with_price(self.price_tag_product, self.price_category)
        )
        self.assertTrue(
            match_price_tag_with_price(self.price_tag_category, self.price_category)
        )
        self.assertFalse(
            match_price_tag_with_price(self.price_tag_category, self.price_product)
        )
        # add extra prices with the same price
        PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="0123456789101",
            price=1.5,
            proof=self.proof,
            location=self.proof.location,
        )
        self.assertFalse(
            match_price_tag_with_price(self.price_tag_product, self.price_product)
        )
        PriceFactory(
            type=price_constants.TYPE_CATEGORY,
            category_tag="en:apples",
            price=2.5,
            price_per=price_constants.PRICE_PER_KILOGRAM,
            proof=self.proof,
            location=self.proof.location,
        )
        self.assertFalse(
            match_price_tag_with_price(self.price_tag_category, self.price_category)
        )


class ReceiptItemQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        cls.price = PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="8001505005707",
            price=10,
            proof=cls.proof,
            location=cls.proof.location,
        )
        cls.receipt_item = ReceiptItemFactory(
            predicted_data={"product_name": "NOCCIOLATA 700G", "price": 10},
            proof=cls.proof,
            price=cls.price,
            status=proof_constants.ReceiptItemStatus.linked_to_price.value,
        )
        ReceiptItemFactory(
            predicted_data={"product_name": "Nutella", "price": 5},
            proof=cls.proof,
        )

    def test_status_unknown(self):
        self.assertEqual(ReceiptItem.objects.count(), 2)
        self.assertEqual(ReceiptItem.objects.status_unknown().count(), 1)

    def test_status_linked_to_price(self):
        self.assertEqual(ReceiptItem.objects.count(), 2)
        self.assertEqual(ReceiptItem.objects.status_linked_to_price().count(), 1)

    def test_has_price_product_name_empty(self):
        self.assertEqual(ReceiptItem.objects.count(), 2)
        self.assertEqual(ReceiptItem.objects.has_price_product_name_empty().count(), 2)
        Price.objects.filter(id=self.price.id).update(product_name="NOCCIOLATA 700G")
        self.assertEqual(ReceiptItem.objects.has_price_product_name_empty().count(), 1)


class ReceiptItemPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        cls.price = PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="8001505005707",
            price=10,
            proof=cls.proof,
            location=cls.proof.location,
        )
        cls.receipt_item = ReceiptItemFactory(
            predicted_data={"product_name": "NOCCIOLATA 700G", "price": 10},
            proof=cls.proof,
            price=cls.price,
            status=proof_constants.ReceiptItemStatus.linked_to_price.value,
        )
        cls.receipt_item_empty = ReceiptItemFactory(
            predicted_data={},
            proof=cls.proof,
        )

    def test_get_predicted_price(self):
        self.assertEqual(self.receipt_item.get_predicted_price(), 10)
        self.assertEqual(self.receipt_item_empty.get_predicted_price(), None)

    def test_get_predicted_product_name(self):
        self.assertEqual(
            self.receipt_item.get_predicted_product_name(), "NOCCIOLATA 700G"
        )
        self.assertEqual(self.receipt_item_empty.get_predicted_product_name(), None)


class ReceiptItemMatchingUtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof = ProofFactory(type=proof_constants.TYPE_RECEIPT)
        cls.receipt_item = ReceiptItemFactory(
            predicted_data={"product_name": "NOCCIOLATA 700G", "price": 10},
            proof=cls.proof,
        )
        cls.price = PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="8001505005707",
            price=10,
            proof=cls.proof,
            location=cls.proof.location,
        )

    def test_match_receipt_item_with_price(self):
        self.assertTrue(match_receipt_item_with_price(self.receipt_item, self.price))
        # add an extra price with the same price
        PriceFactory(
            type=price_constants.TYPE_PRODUCT,
            product_code="0123456789101",
            price=10,
            proof=self.proof,
            location=self.proof.location,
        )
        self.assertFalse(match_receipt_item_with_price(self.receipt_item, self.price))
