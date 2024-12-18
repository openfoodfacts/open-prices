import enum
import json
import logging
from pathlib import Path

import google.generativeai as genai
import typing_extensions as typing
from django.conf import settings
from openfoodfacts.ml.image_classification import ImageClassifier
from openfoodfacts.ml.object_detection import ObjectDetectionRawResult, ObjectDetector
from PIL import Image

from . import constants
from .models import PriceTag, PriceTagPrediction, Proof, ProofPrediction

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
GEMINI_MODEL_NAME = "gemini"
GEMINI_MODEL_VERSION = "gemini-1.5-flash"

genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=GEMINI_MODEL_VERSION)


# TODO: what about other categories?
class Products(enum.Enum):
    OTHER = "other"
    APPLES = "en:apples"
    APRICOTS = "en:apricots"
    ARTICHOKES = "en:artichokes"
    ASPARAGUS = "en:asparagus"
    AUBERGINES = "en:aubergines"
    AVOCADOS = "en:avocados"
    BANANAS = "en:bananas"
    BEET = "en:beet"
    BERRIES = "en:berries"
    BLACKBERRIES = "en:blackberries"
    BLUEBERRIES = "en:blueberries"
    BOK_CHOY = "en:bok-choy"
    BROCCOLI = "en:broccoli"
    CABBAGES = "en:cabbages"
    CARROTS = "en:carrots"
    CAULIFLOWERS = "en:cauliflowers"
    CELERY = "en:celery"
    CELERY_STALK = "en:celery-stalk"
    CEP_MUSHROOMS = "en:cep-mushrooms"
    CHANTERELLES = "en:chanterelles"
    CHERRIES = "en:cherries"
    CHERRY_TOMATOES = "en:cherry-tomatoes"
    CHICKPEAS = "en:chickpeas"
    CHIVES = "en:chives"
    CLEMENTINES = "en:clementines"
    COCONUTS = "en:coconuts"
    CRANBERRIES = "en:cranberries"
    CUCUMBERS = "en:cucumbers"
    DATES = "en:dates"
    ENDIVES = "en:endives"
    FIGS = "en:figs"
    GARLIC = "en:garlic"
    GINGER = "en:ginger"
    GRAPEFRUITS = "en:grapefruits"
    GRAPES = "en:grapes"
    GREEN_BEANS = "en:green-beans"
    KIWIS = "en:kiwis"
    KAKIS = "en:kakis"
    LEEKS = "en:leeks"
    LEMONS = "en:lemons"
    LETTUCES = "en:lettuces"
    LIMES = "en:limes"
    LYCHEES = "en:lychees"
    MANDARIN_ORANGES = "en:mandarin-oranges"
    MANGOES = "en:mangoes"
    MELONS = "en:melons"
    MUSHROOMS = "en:mushrooms"
    NECTARINES = "en:nectarines"
    ONIONS = "en:onions"
    ORANGES = "en:oranges"
    PAPAYAS = "en:papayas"
    PASSION_FRUITS = "en:passion-fruits"
    PEACHES = "en:peaches"
    PEARS = "en:pears"
    PEAS = "en:peas"
    PEPPERS = "en:peppers"
    PINEAPPLE = "en:pineapple"
    PLUMS = "en:plums"
    POMEGRANATES = "en:pomegranates"
    POMELOS = "en:pomelos"
    POTATOES = "en:potatoes"
    PUMPKINS = "en:pumpkins"
    RADISHES = "en:radishes"
    RASPBERRIES = "en:raspberries"
    RHUBARBS = "en:rhubarbs"
    SCALLIONS = "en:scallions"
    SHALLOTS = "en:shallots"
    SPINACHS = "en:spinachs"
    SPROUTS = "en:sprouts"
    STRAWBERRIES = "en:strawberries"
    TOMATOES = "en:tomatoes"
    TURNIP = "en:turnip"
    WATERMELONS = "en:watermelons"
    WALNUTS = "en:walnuts"
    ZUCCHINI = "en:zucchini"


# TODO: what about other origins?
class Origin(enum.Enum):
    FRANCE = "en:france"
    ITALY = "en:italy"
    SPAIN = "en:spain"
    POLAND = "en:poland"
    CHINA = "en:china"
    BELGIUM = "en:belgium"
    MOROCCO = "en:morocco"
    PERU = "en:peru"
    PORTUGAL = "en:portugal"
    MEXICO = "en:mexico"
    OTHER = "other"
    UNKNOWN = "unknown"


class Unit(enum.Enum):
    KILOGRAM = "KILOGRAM"
    UNIT = "UNIT"


class Label(typing.TypedDict):
    product: Products
    price: float
    origin: Origin
    unit: Unit
    organic: bool
    barcode: str


class Labels(typing.TypedDict):
    labels: list[Label]


def extract_from_price_tags(images: Image.Image) -> Labels:
    """Extract price tag information from a list of images."""
    response = model.generate_content(
        [
            "Here are "
            + str(len(images))
            + " pictures containing a label. For each picture of a label, please extract all the following attributes: the product category matching product name, the origin category matching country of origin, the price, is the product organic, the unit (per KILOGRAM or per UNIT) and the barcode. I expect a list of "
            + str(len(images))
            + " labels in your reply, no more, no less. If you cannot decode an attribute, set it to an empty string"
        ]
        + images,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", response_schema=Labels
        ),
    )
    return json.loads(response.text)


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


def run_and_save_price_tag_extraction_from_id(price_tag_id: int) -> None:
    """Extract information from a single price tag using the Gemini model and
    save the predictions in the database.

    This function is meant to be called asynchronously using django background
    tasks.

    :param price_tag_id the ID of the PriceTag instance to extract information
    """
    price_tag = PriceTag.objects.filter(id=price_tag_id).select_related("proof").first()

    if not price_tag:
        logger.error("Price tag with id %s not found", price_tag_id)
        return None

    run_and_save_price_tag_extraction([price_tag], price_tag.proof)


def run_and_save_price_tag_extraction(
    price_tags: list[PriceTag], proof: Proof
) -> list[PriceTagPrediction]:
    """Extract information from price tags using the Gemini model and save the
    predictions in the database.

    :param price_tags: the list of PriceTag instances to extract information
        from
    :param proof: the Proof instance associated with the price tags
    :return: the list of PriceTagPrediction instances created
    """
    if proof.file_path_full is None or not Path(proof.file_path_full).exists():
        logger.error("Proof file not found: %s", proof.file_path_full)
        return []

    cropped_images = []
    for price_tag in price_tags:
        y_min, x_min, y_max, x_max = price_tag.bounding_box
        image = Image.open(proof.file_path_full)
        (left, right, top, bottom) = (
            x_min * image.width,
            x_max * image.width,
            y_min * image.height,
            y_max * image.height,
        )
        cropped_image = image.crop((left, top, right, bottom))
        cropped_images.append(cropped_image)

    labels = extract_from_price_tags(cropped_images)

    predictions = []
    for price_tag, label in zip(price_tags, labels["labels"]):
        prediction = PriceTagPrediction.objects.create(
            price_tag=price_tag,
            type=constants.PRICE_TAG_EXTRACTION_TYPE,
            model_name=GEMINI_MODEL_NAME,
            model_version=GEMINI_MODEL_VERSION,
            data=label,
        )
        predictions.append(prediction)

    return predictions


def update_price_tag_extraction(price_tag_id: int) -> PriceTagPrediction:
    """Update the price tag extraction prediction using the Gemini model.

    :param price_tag: the PriceTag instance associated with the prediction
    :return: the updated PriceTagPrediction instance
    """
    price_tag = PriceTag.objects.filter(id=price_tag_id).select_related("proof").first()

    if not price_tag:
        logger.error("Price tag with id %s not found", price_tag_id)
        return None

    proof = price_tag.proof
    if proof.file_path_full is None or not Path(proof.file_path_full).exists():
        logger.error("Proof file not found: %s", proof.file_path_full)
        return []

    price_tag_prediction = PriceTagPrediction.objects.filter(
        price_tag=price_tag, type=constants.PRICE_TAG_EXTRACTION_TYPE
    ).first()

    if not price_tag_prediction:
        logger.info(
            "Price tag %s does not have a price tag extraction prediction",
            price_tag.id,
        )
        return None

    y_min, x_min, y_max, x_max = price_tag.bounding_box
    image = Image.open(proof.file_path_full)
    (left, right, top, bottom) = (
        x_min * image.width,
        x_max * image.width,
        y_min * image.height,
        y_max * image.height,
    )
    cropped_image = image.crop((left, top, right, bottom))
    gemini_output = extract_from_price_tags([cropped_image])
    price_tag_prediction.data = gemini_output["labels"][0]
    price_tag_prediction.model_name = GEMINI_MODEL_NAME
    price_tag_prediction.model_version = GEMINI_MODEL_VERSION
    price_tag_prediction.save()
    return price_tag_prediction


def create_price_tags_from_proof_prediction(
    proof: Proof,
    proof_prediction: ProofPrediction,
    threshold: float = 0.5,
    run_extraction: bool = True,
) -> list[PriceTag]:
    """Create price tags from a proof prediction containing price tag object
    detections.

    :param proof: the Proof instance to associate the PriceTag instances with
    :param proof_prediction: the ProofPrediction instance containing the
        price tag detections
    :param threshold: the minimum confidence threshold for a detection to be
        considered valid, defaults to 0.5
    :param run_extraction: whether to run the price tag extraction model on the
        detected price tags, defaults to True
    :return: the list of PriceTag instances created
    """
    if proof_prediction.model_name != PRICE_TAG_DETECTOR_MODEL_NAME:
        logger.error(
            "Proof prediction model %s is not a price tag detector",
            proof_prediction.model_name,
        )
        return []

    created = []
    for detected_object in proof_prediction.data["objects"]:
        if detected_object["score"] >= threshold:
            price_tag = PriceTag.objects.create(
                proof=proof,
                bounding_box=detected_object["bounding_box"],
                model_version=proof_prediction.model_version,
                status=None,
                created_by=None,
                updated_by=None,
            )
            created.append(price_tag)

    if run_extraction:
        run_and_save_price_tag_extraction(created, proof)

    return created


def run_and_save_price_tag_detection(
    image: Image, proof: Proof, overwrite: bool = False, run_extraction: bool = True
) -> ProofPrediction | None:
    """Run the price tag object detection model and save the prediction
    in ProofPrediction table.

    :param image: the image to run the model on
    :param proof: the Proof instance to associate the ProofPrediction with
    :param overwrite: whether to overwrite existing prediction, defaults to
        False
    :param run_extraction: whether to run the price tag extraction model on the
        detected price tags, defaults to True
    :return: the ProofPrediction instance created, or None if the prediction
        already exists and overwrite is False
    """

    proof_prediction = ProofPrediction.objects.filter(
        proof=proof, model_name=PRICE_TAG_DETECTOR_MODEL_NAME
    ).first()

    if proof_prediction:
        if overwrite:
            logger.info(
                "Overwriting existing price tag detection for proof %s", proof.id
            )
            proof_prediction.delete()
        else:
            logger.debug(
                "Proof %s already has a prediction for model %s",
                proof.id,
                PRICE_TAG_DETECTOR_MODEL_NAME,
            )
            if not PriceTag.objects.filter(proof=proof).exists():
                logger.debug(
                    "Creating price tags from existing prediction for proof %s",
                    proof.id,
                )
                create_price_tags_from_proof_prediction(
                    proof, proof_prediction, run_extraction=run_extraction
                )
            return None

    result = detect_price_tags(image)
    detections = result.to_list()
    if detections:
        max_confidence = max(detections, key=lambda x: x["score"])["score"]
    else:
        max_confidence = None

    proof_prediction = ProofPrediction.objects.create(
        proof=proof,
        type=constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
        model_name=PRICE_TAG_DETECTOR_MODEL_NAME,
        model_version=PRICE_TAG_DETECTOR_MODEL_VERSION,
        data={"objects": detections},
        value=None,
        max_confidence=max_confidence,
    )
    create_price_tags_from_proof_prediction(
        proof, proof_prediction, run_extraction=run_extraction
    )
    return proof_prediction


def run_and_save_proof_type_prediction(
    image: Image, proof: Proof, overwrite: bool = False
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
    return ProofPrediction.objects.create(
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


def run_and_save_proof_prediction(
    proof_id: int, run_price_tag_extraction: bool = True
) -> None:
    """Run all ML models on a specific proof, and save the predictions in DB.

    Currently, the following models are run:

    - proof type classification model
    - price tag detection model (objecct detector)

    :param proof_id: the ID of the proof to be classified
    :param run_price_tag_extraction: whether to run the price tag extraction
        model on the detected price tags, defaults to True
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
    run_and_save_price_tag_detection(
        image, proof, run_extraction=run_price_tag_extraction
    )
