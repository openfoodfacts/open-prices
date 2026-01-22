"""
Proof ML/AI
- predict Proof type with triton
- detect Proof's PriceTags with triton
- extract data from PriceTags with Gemini
"""

import logging
from pathlib import Path

from PIL import Image

from open_prices.proofs.ml.classification import run_and_save_proof_type_prediction
from open_prices.proofs.ml.price_tags import run_and_save_price_tag_detection
from open_prices.proofs.ml.receipts import run_and_save_receipt_extraction_prediction
from open_prices.proofs.models import Proof

logger = logging.getLogger(__name__)


def run_and_save_proof_prediction(
    proof: Proof,
    run_price_tag_extraction: bool = True,
    run_receipt_extraction: bool = True,
) -> None:
    """Run all ML models on a specific proof, and save the predictions in DB.

    Currently, the following models are run:

    - proof type classification model
    - price tag detection model (object detector)
    - price tag extraction model
    - receipt extraction model

    :param proof: the Proof object to be classified
    :param run_price_tag_extraction: whether to run the price tag extraction
        model on the detected price tags, defaults to True
    """
    try:
        proof = Proof.objects.get(id=proof.id)
    except Proof.DoesNotExist:
        logger.warning(
            "Proof with id %s no longer exists, skipping ML prediction", proof.id
        )
        return None

    file_path_full = proof.file_path_full

    if file_path_full is None or not Path(file_path_full).exists():
        logger.error("Proof file not found: %s", file_path_full)
        return None

    if Path(file_path_full).suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        logger.debug("Skipping %s, not a supported image type", file_path_full)
        return None

    image = Image.open(file_path_full)
    run_and_save_proof_type_prediction(image, proof)
    run_and_save_price_tag_detection(
        image, proof, run_extraction=run_price_tag_extraction
    )
    if run_receipt_extraction:
        run_and_save_receipt_extraction_prediction(image, proof)
