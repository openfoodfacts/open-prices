import logging
from pathlib import Path

from django.conf import settings
from openfoodfacts.ml.image_classification import ImageClassifier
from openfoodfacts.ml.object_detection import ObjectDetectionRawResult, ObjectDetector
from PIL import Image

from . import constants
from .models import Proof, ProofPrediction

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
PROOF_CLASSIFICATION_TRITON_VERSION = "1"
PRICE_TAG_DETECTOR_LABEL_NAMES = ["price_tag"]
PRICE_TAG_DETECTOR_MODEL_NAME = "price_tag_detection"
PRICE_TAG_DETECTOR_MODEL_VERSION = "price_tag_detection-1.0"
PRICE_TAG_DETECTOR_TRITON_VERSION = "1"
PRICE_TAG_DETECTOR_IMAGE_SIZE = 960


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


def detect_price_tags(
    image: Image.Image,
    model_name: str = PRICE_TAG_DETECTOR_MODEL_NAME,
    model_version: str = PRICE_TAG_DETECTOR_TRITON_VERSION,
    label_names: list[str] = PRICE_TAG_DETECTOR_LABEL_NAMES,
    image_size: int = PRICE_TAG_DETECTOR_IMAGE_SIZE,
    triton_uri: str = settings.TRITON_URI,
    threshold: float = 0.5,
) -> ObjectDetectionRawResult:
    """Detect the price tags in a proof image.

    :param image: the input Pillow image
    :param model_version: the version of the model to use, defaults to
        MODEL_VERSION
    :param model_name: the name of the model to use, defaults to MODEL_NAME
    :param label_names: the names of the labels, defaults to
        PROOF_CLASSIFICATION_LABEL_NAMES
    :param image_size: the size of the image, defaults to IMAGE_SIZE
    :param triton_uri: the URI of the Triton server, defaults to
        settings.TRITON_URI
    :return: the detection results
    """
    detector = ObjectDetector(
        model_name=model_name,
        label_names=label_names,
        image_size=image_size,
    )
    return detector.detect_from_image(
        image, triton_uri=triton_uri, threshold=threshold, model_version=model_version
    )


def run_and_save_price_tag_detection(image: Image, proof: Proof) -> None:
    """Run the price tag object detection model and save the prediction
    in ProofPrediction table.

    :param image: the image to run the model on
    :param proof: the Proof instance to associate the ProofPrediction with
    """
    result = detect_price_tags(image)
    detections = result.to_list()
    if detections:
        max_confidence = max(detections, key=lambda x: x["score"])["score"]
    else:
        max_confidence = None

    ProofPrediction.objects.create(
        proof=proof,
        type=constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
        model_name=PRICE_TAG_DETECTOR_MODEL_NAME,
        model_version=PRICE_TAG_DETECTOR_MODEL_VERSION,
        data={"objects": detections},
        value=None,
        max_confidence=max_confidence,
    )


def run_and_save_proof_type_prediction(image: Image, proof: Proof) -> None:
    """Run the proof type classifier model and save the prediction in
    ProofPrediction table.

    :param image: the image to run the model on
    :param proof: the Proof instance to associate the ProofPrediction with
    """
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


def run_and_save_proof_prediction(proof_id: int) -> None:
    """Run all ML models on a specific proof, and save the predictions in DB.

    Currently, the following models are run:

    - proof type classification model
    - price tag detection model (objecct detector)

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
    run_and_save_proof_type_prediction(image, proof)
    run_and_save_price_tag_detection(image, proof)
