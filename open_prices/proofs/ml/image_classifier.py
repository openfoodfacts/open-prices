import logging
from pathlib import Path

from django.conf import settings
from openfoodfacts.ml.image_classification import ImageClassifier
from PIL import Image

from .. import constants
from ..models import Proof, ProofPrediction

logger = logging.getLogger(__name__)


PROOF_CLASSIFICATION_LABEL_NAMES = [
    "OTHER",
    "PRICE_TAG",
    "PRODUCT_WITH_PRICE",
    "RECEIPT",
    "SHELF",
    "WEB_PRINT",
]
PROOF_CLASSIFICATION_MODEL_NAME = "price_proof_classification"
PROOF_CLASSIFICATION_MODEL_VERSION = "price_proof_classification-1.0"
MODEL_VERSION = "1"


def predict_proof_type(
    image: Image.Image, model_version: str = MODEL_VERSION
) -> list[tuple[str, float]]:
    """Predict the type of a proof image.

    :param image: the input Pillow image
    :param model_version: the version of the model to use
    :return: the prediction results as a list of tuples (label, confidence)
    """
    classifier = ImageClassifier(
        model_name=PROOF_CLASSIFICATION_MODEL_NAME,
        label_names=PROOF_CLASSIFICATION_LABEL_NAMES,
    )
    return classifier.predict(
        image, triton_uri=settings.TRITON_URI, model_version=model_version
    )


def run_and_save_proof_prediction(proof_id: int) -> None:
    """Run the proof classification model on a proof image and save the
    results in DB.

    :param proof_id: the ID of the proof to be classified
    """
    proof = Proof.objects.filter(id=proof_id).first()
    if not proof:
        logger.error("Proof with id %s not found", proof_id)
        return

    file_path_full = proof.file_path_full

    if file_path_full is None or not Path(file_path_full).exists():
        logger.error("Proof file not found: %s", file_path_full)
        return

    if Path(file_path_full).suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        logger.debug("Skipping %s, not a supported image type", file_path_full)
        return None

    image = Image.open(file_path_full)
    prediction = predict_proof_type(image)

    max_confidence = max(prediction, key=lambda x: x[1])[1]
    proof_type = max(prediction, key=lambda x: x[1])[0]
    ProofPrediction.objects.create(
        proof=proof,
        type=constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
        model_name=PROOF_CLASSIFICATION_MODEL_NAME,
        model_version=PROOF_CLASSIFICATION_MODEL_VERSION,
        data={
            "prediction": [
                {"label": label, "score": confidence}
                for label, confidence in prediction
            ]
        },
        value=proof_type,
        max_confidence=max_confidence,
    )
