import unittest
from unittest.mock import patch

import numpy as np
from django.test import TestCase
from pydantic_ai import capture_run_messages, models
from pydantic_ai.messages import BinaryContent
from pydantic_ai.models.test import TestModel

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.factories import ProofFactory, ProofPredictionFactory
from open_prices.proofs.ml.receipt_anonymization import (
    AnonymizationResult,
    PersonalInfo,
    PersonalInfoList,
    Word,
    add_margin_bounding_box,
    anonymize_receipt,
    extract_personal_info,
    run_and_save_receipt_anonymization_prediction,
)
from open_prices.proofs.ml.receipt_anonymization.ocr import OcrResult
from open_prices.proofs.models import ProofPrediction

# Disable calling real LLMs. See:
# https://pydantic.dev/docs/ai/api/models/base/#pydantic_ai.models.ALLOW_MODEL_REQUESTS
models.ALLOW_MODEL_REQUESTS = False  # type: ignore


def check_almost_equal_bounding_box(case_instance, word, expected_box):
    for i in range(4):
        case_instance.assertAlmostEqual(word.bounding_box[i], expected_box[i], places=5)


class TestRunAndSaveReceiptAnonymizationPrediction(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proof_receipt = ProofFactory(type=proof_constants.TYPE_RECEIPT, draft=True)
        cls.proof_receipt_not_draft = ProofFactory(
            type=proof_constants.TYPE_RECEIPT, draft=False
        )
        cls.proof_not_receipt = ProofFactory(type=proof_constants.TYPE_PRICE_TAG)
        cls.image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cls.default_anonymization_result = AnonymizationResult(
            words=[Word(text="NAME", bounding_box=(0, 0, 1.0, 1.0))]
        )

    @patch("open_prices.proofs.ml.receipt_anonymization.anonymize_receipt")
    def test_proof_is_not_a_receipt(self, mock_anonymize_receipt):
        with self.assertLogs(level="DEBUG") as log_cm:
            run_and_save_receipt_anonymization_prediction(
                image=self.image,
                proof=self.proof_not_receipt,
            )
            self.assertEqual(len(log_cm.output), 1)
            self.assertEqual(
                log_cm.output[0],
                f"DEBUG:open_prices.proofs.ml.receipt_anonymization:Skipping proof {self.proof_not_receipt.pk}, not of type RECEIPT",
            )
        assert mock_anonymize_receipt.called is False

    @patch(
        "open_prices.proofs.ml.receipt_anonymization.anonymize_receipt",
    )
    def test_proof_prediction_already_exists(self, mock_anonymize_receipt):
        ProofPredictionFactory(
            proof=self.proof_receipt,
            type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
        )
        with self.assertLogs(level="DEBUG") as log_cm:
            run_and_save_receipt_anonymization_prediction(
                image=self.image,
                proof=self.proof_receipt,
            )
            self.assertEqual(len(log_cm.output), 1)
            self.assertEqual(
                log_cm.output[0],
                f"DEBUG:open_prices.proofs.ml.receipt_anonymization:Proof {self.proof_receipt.pk} already has an anonymization prediction",
            )
        self.assertFalse(mock_anonymize_receipt.called)

    @patch("open_prices.proofs.ml.receipt_anonymization.anonymize_receipt")
    def test_proof_prediction_standard_run(self, mock_anonymize_receipt):
        mock_anonymize_receipt.return_value = self.default_anonymization_result
        run_and_save_receipt_anonymization_prediction(
            image=self.image,
            proof=self.proof_receipt,
        )
        self.assertTrue(mock_anonymize_receipt.called)
        # Check that the proof_prediction doesn't exist anymore
        proof_predictions = ProofPrediction.objects.filter(
            proof=self.proof_receipt,
            type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
        )
        self.assertEqual(len(proof_predictions), 1)
        new_proof_prediction = proof_predictions[0]
        self.assertEqual(
            new_proof_prediction.data,
            {
                "words": [
                    {
                        "text": "NAME",
                        "bounding_box": [0, 0, 1.0, 1.0],
                        "line_idx": None,
                    }
                ]
            },
        )

    @patch(
        "open_prices.proofs.ml.receipt_anonymization.anonymize_receipt",
    )
    def test_proof_prediction_proof_not_draft(self, mock_anonymize_receipt):
        with self.assertLogs(level="DEBUG") as log_cm:
            run_and_save_receipt_anonymization_prediction(
                image=self.image,
                proof=self.proof_receipt_not_draft,
            )
            self.assertEqual(len(log_cm.output), 1)
            self.assertEqual(
                log_cm.output[0],
                (
                    "INFO:open_prices.proofs.ml.receipt_anonymization:Proof is not "
                    "a draft: it was probably finalized before prediction was ready. "
                    "The receipt anonymization prediction will not be saved."
                ),
            )
        self.assertTrue(mock_anonymize_receipt.called)
        self.assertEqual(
            ProofPrediction.objects.filter(
                proof=self.proof_receipt_not_draft,
                type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
            ).count(),
            0,
        )

    @patch("open_prices.proofs.ml.receipt_anonymization.anonymize_receipt")
    def test_proof_prediction_already_exists_overwrite(self, mock_anonymize_receipt):
        mock_anonymize_receipt.return_value = self.default_anonymization_result
        proof_prediction = ProofPredictionFactory(
            proof=self.proof_receipt,
            type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
        )
        with self.assertLogs(level="DEBUG") as log_cm:
            run_and_save_receipt_anonymization_prediction(
                image=self.image,
                proof=self.proof_receipt,
                overwrite=True,
            )
            self.assertTrue(mock_anonymize_receipt.called)
            # Check that the proof_prediction doesn't exist anymore
            self.assertEqual(
                ProofPrediction.objects.filter(id=proof_prediction.id).count(), 0
            )
            proof_predictions = ProofPrediction.objects.filter(
                proof=self.proof_receipt,
                type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
            )
            self.assertEqual(len(proof_predictions), 1)
            self.assertEqual(len(log_cm.output), 1)
            self.assertEqual(
                log_cm.output[0],
                f"INFO:open_prices.proofs.ml.receipt_anonymization:Overwriting existing anonymization prediction for proof {self.proof_receipt.pk}",
            )


class TestExtractPersonalInfo(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.small_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cls.model_name = "minimax/minimax-m3"

    @patch("open_prices.proofs.ml.receipt_anonymization.get_pydantic_ai_model")
    def test_standard_run(self, mock_get_pydantic_ai_model):
        mock_get_pydantic_ai_model.return_value = TestModel()
        with capture_run_messages() as messages:
            info = extract_personal_info(self.small_image, self.model_name)
            self.assertIsInstance(info, PersonalInfoList)
            self.assertEqual(len(messages), 3)
            first_message = messages[0]
            self.assertEqual(len(first_message.parts), 1)
            user_prompt_content = first_message.parts[0].content
            self.assertEqual(len(user_prompt_content), 2)
            self.assertEqual(
                user_prompt_content[0],
                (
                    "Identify the following personal information from this receipt:\n"
                    "- name of the supermarket cashier, if any. It should only be "
                    "included in the results if the first name and/or last name of "
                    "the cashier is mentioned.\n"
                    "- name of the buyer (who may have used a fidelity card). Some street "
                    "names may contain name of people (as the address of the shop is "
                    "often displayed on the receipt), but they should not be included in "
                    "the results.\n"
                    "- fidelity card ID\n\n"
                    "For the value:\n"
                    "- don't change the formatting, keep the value as it is displayed on "
                    "the receipt.\n- only include the personal information, not the suffix "
                    "(ex: don't include 'fidelity card ID:', but only the ID).\n"
                ),
            )
            self.assertIsInstance(
                user_prompt_content[1],
                BinaryContent,
            )


class TestAddMarginBoundingBox(unittest.TestCase):
    def test_add_margin_bounding_box(self):
        """Tests add_margin_bounding_box with various configurations."""
        # Test 1: No margin (default)
        word = Word(text="HELLO", bounding_box=(0.1, 0.2, 0.5, 0.8))
        add_margin_bounding_box(word)
        self.assertEqual(word.bounding_box, (0.1, 0.2, 0.5, 0.8))

        # Test 2: Both margins (multi-char word)
        word = Word(text="HELLO", bounding_box=(0.1, 0.2, 0.5, 0.8))
        add_margin_bounding_box(word, left_margin=1.0, right_margin=1.0)
        # Width = 0.5 - 0.1 = 0.4
        # Left: 0.1 - 1.0 * 0.4 / 5 = 0.1 - 0.08 = 0.02
        # Right: 0.5 + 1.0 * 0.4 / 5 = 0.5 + 0.08 = 0.58
        check_almost_equal_bounding_box(self, word, (0.02, 0.2, 0.58, 0.8))

        # Test 3: Single-character word (left margin x2.5)
        word = Word(text="A", bounding_box=(0.1, 0.2, 0.5, 0.8))
        add_margin_bounding_box(word, left_margin=1.0, right_margin=1.0)
        # Width = 0.5 - 0.1 = 0.4
        # Left: 0.1 - 2.5 * 1.0 * 0.4 / 1 = 0.1 - 1.0 = -0.9 -> clamped to 0.0
        # Right: 0.5 + 1.0 * 0.4 / 1 = 0.5 + 0.4 = 0.9
        check_almost_equal_bounding_box(self, word, (0.0, 0.2, 0.9, 0.8))

        # Test 4: Clamping to [0, 1]
        word = Word(text="HI", bounding_box=(0.0, 0.0, 1.0, 1.0))
        add_margin_bounding_box(word, left_margin=10.0, right_margin=10.0)
        # Left: 0.0 - 10.0 * 1.0 / 2 = -5.0 -> clamped to 0.0
        # Right: 1.0 + 10.0 * 1.0 / 2 = 6.0 -> clamped to 1.0
        check_almost_equal_bounding_box(self, word, (0.0, 0.0, 1.0, 1.0))


class TestAnonymizeReceipt(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.small_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cls.model_name = "minimax/minimax-m3"

    @patch("open_prices.proofs.ml.receipt_anonymization.extract_personal_info")
    @patch("open_prices.proofs.ml.receipt_anonymization.run_ocr")
    def test_standard_run(self, mock_run_ocr, mock_extract_personal_info):
        mock_extract_personal_info.return_value = PersonalInfoList(
            items=[PersonalInfo(type="name", value="Mr. Dupont")]
        )
        words = [
            Word(text="Mr.", bounding_box=(0.1, 0.5, 0.12, 0.55)),
            Word(text="Dupont", bounding_box=(0.14, 0.5, 0.16, 0.55)),
        ]
        mock_run_ocr.return_value = OcrResult(words=words)
        result = anonymize_receipt(
            self.small_image, model=self.model_name, add_margin=False
        )
        self.assertIsInstance(result, AnonymizationResult)
        self.assertEqual(result.words, words)

    @patch("open_prices.proofs.ml.receipt_anonymization.extract_personal_info")
    @patch("open_prices.proofs.ml.receipt_anonymization.run_ocr")
    def test_run_with_add_margin(self, mock_run_ocr, mock_extract_personal_info):
        mock_extract_personal_info.return_value = PersonalInfoList(
            items=[PersonalInfo(type="name", value="Mr. Dupont")]
        )
        words = [
            Word(text="Mr.", bounding_box=(0.1, 0.5, 0.14, 0.55)),
            Word(text="Dupont", bounding_box=(0.16, 0.5, 0.22, 0.55)),
        ]
        mock_run_ocr.return_value = OcrResult(words=words)
        result = anonymize_receipt(
            self.small_image, model=self.model_name, add_margin=True
        )
        self.assertIsInstance(result, AnonymizationResult)
        self.assertEqual(len(result.words), 2)
        first_word = result.words[0]
        self.assertEqual(first_word.text, "Mr.")
        check_almost_equal_bounding_box(
            self, first_word, (0.0866666, 0.5, 0.1453333, 0.55)
        )
        second_word = result.words[1]
        self.assertEqual(second_word.text, "Dupont")
        check_almost_equal_bounding_box(self, second_word, (0.15, 0.5, 0.224, 0.55))
