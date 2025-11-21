import logging

from django.conf import settings
from openfoodfacts.ml.image_classification import ImageClassifier
from PIL import Image

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import Proof, ProofPrediction

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
PROOF_CLASSIFICATION_TRITON_VERSION = "1"


logger = logging.getLogger(__name__)


def predict_proof_type(
    image: Image.Image,
    model_name: str = PROOF_CLASSIFICATION_MODEL_NAME,
    model_version: str = PROOF_CLASSIFICATION_TRITON_VERSION,
    label_names: list[str] = PROOF_CLASSIFICATION_LABEL_NAMES,
    triton_uri: str = settings.TRITON_URI,
) -> list[tuple[str, float]]:
    """Predict the type of a proof image.

    :param image: the input Pillow image
    :param model_version: the version of the model to use
    :return: the prediction results as a list of tuples (label, confidence)
    """
    classifier = ImageClassifier(
        model_name=model_name,
        label_names=label_names,
    )
    return classifier.predict(
        image,
        triton_uri=triton_uri,
        model_version=model_version,
    )


def run_and_save_proof_type_prediction(
    image: Image.Image, proof: Proof, overwrite: bool = False
) -> ProofPrediction | None:
    """Run the proof type classifier model and save the prediction in
    ProofPrediction table.

    :param image: the image to run the model on
    :param proof: the Proof instance to associate the ProofPrediction with
    :param overwrite: whether to overwrite existing prediction, defaults to
        False
    :return: the ProofPrediction instance created, or None if the prediction
        already exists and overwrite is False
    """
    if ProofPrediction.objects.filter(
        proof=proof, model_name=PROOF_CLASSIFICATION_MODEL_NAME
    ).exists():
        if overwrite:
            logger.info("Overwriting existing type prediction for proof %s", proof.id)
            ProofPrediction.objects.filter(
                proof=proof, model_name=PROOF_CLASSIFICATION_MODEL_NAME
            ).delete()
        else:
            logger.debug(
                "Proof %s already has a prediction for model %s",
                proof.id,
                PROOF_CLASSIFICATION_MODEL_NAME,
            )
            return None

    prediction = predict_proof_type(image)

    max_confidence = max(prediction, key=lambda x: x[1])[1]
    proof_type = max(prediction, key=lambda x: x[1])[0]
    try:
        return ProofPrediction.objects.create(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_CLASSIFICATION_TYPE,
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
    except Exception as e:
        logger.exception(e)
        return None
