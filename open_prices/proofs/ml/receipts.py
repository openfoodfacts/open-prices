import json
import logging

from django.conf import settings
from google import genai
from openfoodfacts.types import JSONType
from PIL import Image

# TypedDict is only available from typing in Python 3.12+, drop
# typing_extensions import when we drop support for older versions
from typing_extensions import TypedDict

from open_prices.common import google as common_google
from open_prices.prices import constants as price_constants
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml.price_tags import Products
from open_prices.proofs.models import Proof, ProofPrediction, ReceiptItem

logger = logging.getLogger(__name__)


class ReceiptItemType(TypedDict):
    product: Products
    price: float
    product_name: str


class Receipt(TypedDict):
    store_name: str
    store_address: str
    store_city_name: str
    date: str
    # currency: str
    # price_count: int
    # price_total: float
    items: list[ReceiptItemType]


def extract_from_receipt(image: Image.Image) -> JSONType | None:
    """Extract receipt information from an image."""
    # Gemini model max payload size is 20MB
    # To prevent the payload from being too large, we resize the images before
    # upload
    max_size = 1024
    if image.width > max_size or image.height > max_size:
        image = image.copy()
        image.thumbnail((max_size, max_size))

    prompt = "Extract all relevant information, use empty strings for unknown values."
    with genai.Client(
        credentials=common_google.get_google_credentials(),
        project=settings.GOOGLE_PROJECT,
    ) as client:
        response = client.models.generate_content(
            model=common_google.GEMINI_MODEL_VERSION,
            contents=[
                prompt,
                image,
            ],
            config=common_google.get_generation_config(
                Receipt, thinking_level="minimal"
            ),
        )
    # Sometimes the response is not valid JSON, we try to parse it and return
    # None
    try:
        return json.loads(response.text) if response.text else None
    except json.JSONDecodeError:
        logger.warning("Error decoding receipt extraction response: %s", response.text)
        return None


def create_receipt_items_from_proof_prediction(
    proof: Proof, proof_prediction: ProofPrediction
) -> list[ReceiptItem]:
    """Create receipt items from a proof prediction containing receipt item
    detections.
    Also looks up Prices table for similar product name and location to try to
    extract the product code.

    :param proof: the Proof instance to associate the ReceiptItems with
    :param proof_prediction: the ProofPrediction instance containing the
        receipt items detections
    :return: the list of ReceiptItem instances created
    """
    if proof_prediction.model_name != common_google.GEMINI_MODEL_NAME:
        logger.error(
            "Proof prediction model %s is not a receipt extraction",
            proof_prediction.model_name,
        )
        return []

    # For every predicted item product name, look up a corresponding Price
    product_names = [
        item.get("product_name")
        for item in proof_prediction.data.get("items", [])
        if item.get("product_name")
    ]
    matching_prices = Price.objects.filter(
        product_name__in=product_names,
        location=proof.location,
        type=price_constants.TYPE_PRODUCT,
    )
    # Using the prices data, create a lookup table matching product names
    # and product codes
    product_lookup: dict[str, str] = {}
    for price in matching_prices:
        if (
            price.product_name in product_lookup
            and product_lookup[price.product_name] != price.product_code
        ):
            logger.warning(
                "Multiple products with the same name found: %s", price.product_name
            )
        product_lookup[price.product_name] = price.product_code

    created = []
    for index, predicted_item in enumerate(proof_prediction.data.get("items", [])):
        # Check if we have a matching product code
        # for the predicted product name
        matching_product_code = product_lookup.get(predicted_item.get("product_name"))
        if matching_product_code:
            predicted_item["predicted_product_code"] = matching_product_code

        receipt_item = ReceiptItem.objects.create(
            proof=proof,
            proof_prediction=proof_prediction,
            price=None,
            order=index + 1,
            predicted_data=predicted_item,
            status=None,
        )
        created.append(receipt_item)
    return created


def run_and_save_receipt_extraction_prediction(
    image: Image.Image, proof: Proof, overwrite: bool = False
) -> ProofPrediction | None:
    """Run the receipt extraction model and save the prediction in
    ProofPrediction table.

    :param image: the image to run the model on
    :param proof: the Proof instance to associate the ProofPrediction with
    :param overwrite: whether to overwrite existing prediction, defaults to
        False
    :return: the ProofPrediction instance created, or None if the prediction
        already exists and overwrite is False
    """
    if proof.type != proof_constants.TYPE_RECEIPT:
        logger.debug("Skipping proof %s, not of type RECEIPT", proof.id)
        return None

    if ProofPrediction.objects.filter(
        proof=proof, model_name=common_google.GEMINI_MODEL_NAME
    ).exists():
        if overwrite:
            logger.info("Overwriting existing type prediction for proof %s", proof.id)
            ProofPrediction.objects.filter(
                proof=proof, model_name=common_google.GEMINI_MODEL_NAME
            ).delete()
        else:
            logger.debug(
                "Proof %s already has a prediction for model %s",
                proof.id,
                common_google.GEMINI_MODEL_NAME,
            )
            return None

    prediction = extract_from_receipt(image)

    try:
        proof_prediction = ProofPrediction.objects.create(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE,
            model_name=common_google.GEMINI_MODEL_NAME,
            model_version=common_google.GEMINI_MODEL_VERSION,
            # prediction may be None if the model failed to extract
            data=prediction or {},
        )
        create_receipt_items_from_proof_prediction(proof, proof_prediction)
        return proof_prediction
    except Exception as e:
        logger.exception(e)
    return None
