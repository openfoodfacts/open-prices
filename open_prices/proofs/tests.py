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
from PIL import Image

from open_prices.locations import constants as location_constants
from open_prices.locations.factories import LocationFactory
from open_prices.prices.factories import PriceFactory
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import (
    PriceTagFactory,
    ProofFactory,
    ProofPredictionFactory,
)
from open_prices.proofs.ml import (
    PRICE_TAG_DETECTOR_MODEL_NAME,
    PRICE_TAG_DETECTOR_MODEL_VERSION,
    PROOF_CLASSIFICATION_MODEL_NAME,
    PROOF_CLASSIFICATION_MODEL_VERSION,
    ObjectDetectionRawResult,
    create_price_tags_from_proof_prediction,
    run_and_save_price_tag_detection,
    run_and_save_proof_prediction,
    run_and_save_proof_type_prediction,
)
from open_prices.proofs.models import PriceTag, Proof
from open_prices.proofs.utils import fetch_and_save_ocr_data, select_proof_image_dir

LOCATION_OSM_NODE_652825274 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 652825274,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Monoprix",
}
LOCATION_OSM_NODE_6509705997 = {
    "type": location_constants.TYPE_OSM,
    "osm_id": 6509705997,
    "osm_type": location_constants.OSM_TYPE_NODE,
    "osm_name": "Carrefour",
}


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

    def test_proof_ready_for_price_tag_validation_field(self):
        proof = ProofFactory(type=proof_constants.TYPE_PRICE_TAG, source="/proofs/add/")
        self.assertFalse(proof.ready_for_price_tag_validation)
        proof.source = "/proofs/add/multiple"
        proof.save()
        self.assertTrue(proof.ready_for_price_tag_validation)


class ProofQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_without_price = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.proof_with_price = ProofFactory(type=proof_constants.TYPE_GDPR_REQUEST)
        PriceFactory(proof_id=cls.proof_with_price.id, price=1.0)

    def test_has_type_single_shop(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_type_single_shop().count(), 1)

    def test_has_prices(self):
        self.assertEqual(Proof.objects.count(), 2)
        self.assertEqual(Proof.objects.has_prices().count(), 1)

    def test_with_stats(self):
        proof = Proof.objects.with_stats().get(id=self.proof_without_price.id)
        self.assertEqual(proof.price_count_annotated, 0)
        self.assertEqual(proof.price_count, 0)
        proof = Proof.objects.with_stats().get(id=self.proof_with_price.id)
        self.assertEqual(proof.price_count_annotated, 1)
        self.assertEqual(proof.price_count, 1)


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
        cls.proof_receipt = ProofFactory(type=proof_constants.TYPE_RECEIPT)
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
                "open_prices.proofs.utils.run_ocr_on_image",
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
    def test_run_and_save_proof_prediction_proof_does_not_exist(self):
        # check that we emit an error log
        with self.assertLogs("open_prices.proofs.ml", level="ERROR") as cm:
            self.assertIsNone(run_and_save_proof_prediction(1))
            self.assertEqual(
                cm.output,
                ["ERROR:open_prices.proofs.ml:Proof with id 1 not found"],
            )

    def test_run_and_save_proof_prediction_proof_file_not_found(self):
        proof = ProofFactory()
        # check that we emit an error log
        with self.assertLogs("open_prices.proofs.ml", level="ERROR") as cm:
            self.assertIsNone(run_and_save_proof_prediction(proof.id))
            self.assertEqual(
                cm.output,
                [
                    f"ERROR:open_prices.proofs.ml:Proof file not found: {proof.file_path_full}"
                ],
            )

    def test_run_and_save_proof_prediction_proof(self):
        # Create a white blank image with Pillow
        image = Image.new("RGB", (100, 100), "white")
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
            image.save(file_path)

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
                        proof.id, run_price_tag_extraction=False
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

                proof_type_prediction.delete()
                price_tag_prediction.delete()
                proof.delete()

    def test_run_and_save_proof_type_prediction_already_exists(self):
        image = Image.new("RGB", (100, 100), "white")

        proof = ProofFactory()
        ProofPredictionFactory(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
            model_name=PROOF_CLASSIFICATION_MODEL_NAME,
            model_version=PROOF_CLASSIFICATION_MODEL_VERSION,
        )
        result = run_and_save_proof_type_prediction(image, proof)
        self.assertIsNone(result)

    def test_run_and_save_price_tag_detection_already_exists(self):
        image = Image.new("RGB", (100, 100), "white")
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
        result = run_and_save_price_tag_detection(image, proof, run_extraction=False)
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


class PriceTagCreationTest(TestCase):
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
