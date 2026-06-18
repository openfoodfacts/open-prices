"""
Proof ML/AI
- predict Proof type with triton
- detect Proof's PriceTags with triton
- extract data from PriceTags with Gemini
"""

import logging
from pathlib import Path

from django_q.tasks import async_task

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml.classification import run_and_save_proof_type_prediction
from open_prices.proofs.ml.price_tags import run_and_save_price_tag_detection
from open_prices.proofs.ml.receipts import run_and_save_receipt_extraction_prediction
from open_prices.proofs.models import Proof
from open_prices.proofs.utils import open_image_cv2

logger = logging.getLogger(__name__)


def run_and_save_proof_prediction(
    proof: Proof,
    run_receipt_extraction: bool = True,
    run_async: bool = False,
) -> None:
    """Run all ML models on a specific proof, and save the predictions in DB.

    Currently, the following models are run:
    - proof type classification model
    - price tag detection model
    - receipt extraction model

    :param proof: the Proof object to be classified
    :param run_receipt_extraction: whether to run the receipt extraction model, defaults to True
    :param run_async: whether to run the ML tasks asynchronously through Django Q, defaults to
        False (runs synchronously).
    """
    file_path_full = proof.file_path_full

    if file_path_full is None or not Path(file_path_full).exists():
        logger.error("Proof file not found: %s", file_path_full)
        return None

    if Path(file_path_full).suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        logger.debug("Skipping %s, not a supported image type", file_path_full)
        return None

    if run_async:
        async_task(
            "open_prices.proofs.ml.classification.run_and_save_proof_type_prediction",
            image=None,
            proof=proof,
        )
        if proof.type == proof_constants.TYPE_PRICE_TAG:
            async_task(
                "open_prices.proofs.ml.price_tags.run_and_save_price_tag_detection",
                image=None,
                proof=proof,
            )
        if run_receipt_extraction and proof.type == proof_constants.TYPE_RECEIPT:
            async_task(
                "open_prices.proofs.ml.receipts.run_and_save_receipt_extraction_prediction",
                image=None,
                proof=proof,
            )

    else:
        # image is an uint8 numpy array in BGR format. BGR is the default format used by OpenCV,
        # while our object detection and classification models expect RGB format.
        # The conversion from BGR to RGB is done on-the-fly in the predict_proof_type and
        # run_and_save_price_tag_detection functions.
        image = open_image_cv2(file_path_full)

        run_and_save_proof_type_prediction(image, proof)

        if proof.type == proof_constants.TYPE_PRICE_TAG:
            run_and_save_price_tag_detection(image, proof)
        if run_receipt_extraction and proof.type == proof_constants.TYPE_RECEIPT:
            run_and_save_receipt_extraction_prediction(image, proof)
