import json
import logging
from typing import Literal

from django.conf import settings
from google import genai
from openfoodfacts.types import JSONType
from PIL import Image
from pydantic import BaseModel, Field

from open_prices.common import google as common_google
from open_prices.prices import constants as price_constants
from open_prices.prices.models import Price
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml.common import DiscountType, RawCategory, Unit
from open_prices.proofs.models import Proof, ProofPrediction, ReceiptItem

logger = logging.getLogger(__name__)


# The schema version must be changed every time we introduce a breaking change
# in the Receipt model.
RECEIPT_SCHEMA_VERSION = "2.0"


class ReceiptItemType(BaseModel):
    type: Literal["PRODUCT", "CATEGORY"] = Field(
        ...,
        description="The type of product the receipt entry is referring to. It should be "
        "`PRODUCT` for packaged products with barcode, and `CATEGORY` for raw "
        "products without barcode. The barcode is usually not displayed on receipts, "
        "so the `CATEGORY` type is often inferred from the product name and from the fact "
        "the product is sold per weight.",
    )
    category_group: str | None = Field(
        ...,
        description="if indicated on the receipt, the name of the category group "
        "of the product entry. Indeed, products are sometimes grouped by category "
        "on the receipt, e.g. 'Fruits & Vegetables', 'Dairy', 'Meat', etc. Set to "
        "null if not displayed.",
    )
    product_code: str | None = Field(
        ...,
        description="the barcode of the product entry, if detected. Product barcodes are "
        "rarely displayed on receipts, but some receipts do show them. If type is `CATEGORY` "
        "or if not detected, set to null.",
    )
    category: str | None = Field(
        None,
        description="The category of the product entry. If type=CATEGORY, this should be set to the "
        "category of the product, such as Apples, Bananas, Tomatoes, etc. The category must be in English, "
        "even if the category is displayed in another language on the price tag. "
        "The category must be the most precise category possible: for example, if the entry label says 'Red Onions', "
        "category should be 'Red onions', and not 'Onions'. "
        "If unknown, or if TYPE=PRODUCT, this should be set to null.",
    )
    category_tag: RawCategory | None = Field(
        ...,
        description="the category of the product entry, mapped to Open Food Facts "
        "category taxonomy. This must only be set if type is `CATEGORY`. "
        "if type is `PRODUCT`, set to null. If no suitable category exists in the mapping, set to"
        "'other'.",
    )
    price_total: float | None = Field(
        ...,
        description="the total price for the product entry. On receipts, we "
        "often have a single line when we buy more than one single product, "
        "with the quantity being displayed next to the price. This field "
        "captures this total price for the entry. Set to null if not "
        "detected.",
    )
    price: float | None = Field(
        ...,
        description="the price of a single item, as displayed on this product "
        "entry. It can be the price per unit (if type is 'PRODUCT' or 'CATEGORY'), or "
        "the price per kilogram/per liter (for type 'CATEGORY' only). Set to null if "
        "not detected.",
    )
    price_without_discount: float | None = Field(
        ...,
        description="the price of a single item, before an optional discount. "
        "It can be the price per unit (if type is 'PRODUCT' or 'CATEGORY'), or "
        "the price per kilogram/per liter (for type 'CATEGORY' only). Set to null if "
        "not detected. If there is no discount (=if `price_is_discounted` is false), "
        "also set this to null.",
    )
    price_is_discounted: bool = Field(
        False,
        description="true if this particular price entry is a discounted price, false otherwise",
    )
    discount_type: DiscountType = Field(
        DiscountType.NO_DISCOUNT,
        description="The type of discount applied to the price entry, if any. "
        "If no discount is applied, this should be set to NO_DISCOUNT. "
        "Possible discount types are: "
        " - QUANTITY: example: buy 1 get 1 free, "
        " - SALE: example: 50% off, "
        " - SEASONAL: example: Christmas sale, "
        " - LOYALTY_PROGRAM: example: 10% off for members, "
        " - EXPIRES_SOON: example: 30% off expiring soon, "
        " - PICK_IT_YOURSELF: example: 5% off for pick-up, "
        " - SECOND_HAND: example: second hand books or clothes, "
        " - OTHER: other types of discounts.",
    )
    quantity: float | int | None = Field(
        ...,
        description="the quantity for the product entry. It is a number, either an integer "
        "(for packaged goods or for fruits and vegetables that can be bought "
        "individually), or a float representing the weight (per kg or per liter), for "
        "fruits, vegetables and raw foods that are sold by weight. Set to "
        "null if not detected.",
    )
    price_per: Unit | None = Field(
        ...,
        description="Unit of the price. Can be one of: KILOGRAM: price is per kg, only if type = CATEGORY; "
        "LITER: price is per liter, only if type = CATEGORY; "
        "UNIT: price is per unit (available for both CATEGORY and PRODUCT types). Set to null if not detected.",
    )
    product_name: str | None = Field(
        ...,
        description="the label describing the product entry on the receipt. "
        "Set to null if not detected.",
    )
    uncertain: bool = Field(
        False,
        description="true if the price entry is uncertain: "
        "1) if the entry is occluded (even partially), or blurred, "
        "2) if there is a reflection preventing accurate price of product name reading, "
        "3) if the image quality is not good enough to read the price. "
        "Otherwise, the value must be false.",
    )


class Receipt(BaseModel):
    store_name: str | None = Field(
        ...,
        description="the name of the store. It should be null if the store is not "
        "known. Example: 'Walmart', 'Monoprix', 'Carrefour Express'",
    )
    store_address: str | None = Field(
        ...,
        description="the address of the store. It should be null if the address is "
        "not known. Example: '44 rue du Midi'",
    )
    store_city_name: str | None = Field(
        ...,
        description="the city of the store location. It should be null if the city "
        "is not known. Example: 'Paris'",
    )
    store_postal_code: str | None = Field(
        ...,
        description="the postal code of the store location. It should be null if "
        "the postal code is not known. Example: '75015'",
    )
    store_phone_number: str | None = Field(
        ...,
        description="the phone number of the store. It should be null if the "
        "phone number is not known. Example: '+33123456789'",
    )
    date: str | None = Field(
        ...,
        description="the date when the receipt was issued, in ISO 8601 format "
        "(YYYY-MM-DD). It should be null if the date is not known. Example: "
        "'2023-10-15'",
    )
    hour: str | None = Field(
        ...,
        description="the hour when the receipt was issued, in HH:MM format. "
        "It should be null if the hour is not known. Example: '14:30'",
    )
    total_price: float | None = Field(
        ...,
        description="the total price of the bought products, after discount, "
        "as displayed on the receipt. It should be null if the total price is "
        "not known. Example: 23.45",
    )
    currency: str | None = Field(
        ...,
        description="the currency of the prices on the receipt, in ISO 4217 "
        "format (e.g. 'USD', 'EUR'). It should be null if the currency is not "
        "known. Example: 'EUR'",
    )
    items: list[ReceiptItemType] = Field(
        ...,
        description="the list of items bought. It should be an empty list if no "
        "items are detected.",
    )


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
            schema_version=proof_prediction.data.get("schema_version"),
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

    # prediction may be None if the model failed to extract
    prediction = extract_from_receipt(image) or {}
    if prediction:
        prediction["schema_version"] = RECEIPT_SCHEMA_VERSION

    try:
        proof_prediction = ProofPrediction.objects.create(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE,
            model_name=common_google.GEMINI_MODEL_NAME,
            model_version=common_google.GEMINI_MODEL_VERSION,
            data=prediction,
        )
        create_receipt_items_from_proof_prediction(proof, proof_prediction)
        return proof_prediction
    except Exception as e:
        logger.exception(e)
    return None
