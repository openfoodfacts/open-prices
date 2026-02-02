import asyncio
import enum
import logging
from pathlib import Path
from typing import Literal

import numpy as np
from asgiref.sync import async_to_sync
from django.conf import settings
from google import genai
from openfoodfacts.barcode import normalize_barcode
from openfoodfacts.ml.object_detection import ObjectDetectionRawResult, ObjectDetector
from PIL import Image
from pydantic import BaseModel, Field, computed_field

from open_prices.common import google as common_google
from open_prices.common import openfoodfacts as common_openfoodfacts
from open_prices.products.models import Product
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import (
    PriceTag,
    PriceTagPrediction,
    Proof,
    ProofPrediction,
)
from open_prices.proofs.utils import crop_image

from .common import DiscountType, RawCategory, Unit

PRICE_TAG_DETECTOR_LABEL_NAMES = ["price_tag"]
PRICE_TAG_DETECTOR_MODEL_NAME = "price_tag_detection"
PRICE_TAG_DETECTOR_MODEL_VERSION = "price_tag_detection-1.0"
PRICE_TAG_DETECTOR_TRITON_VERSION = "1"
PRICE_TAG_DETECTOR_IMAGE_SIZE = 960


logger = logging.getLogger(__name__)


# TODO: what about other origins?
class Origin(enum.StrEnum):
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


class SelectedPrice(BaseModel):
    price: float = Field(..., description="Price in the local currency")
    currency: str | None = Field(
        ...,
        description="Currency of the price.",
    )
    price_per: Unit = Field(..., description="Unit of the price")
    price_is_discounted: bool = Field(
        False, description="true if the price is discounted, false otherwise"
    )
    price_without_discount: float | None = Field(
        ...,
        description="The price without discount, if the price is discounted. "
        "If the price is not discounted, this should be set to None.",
    )
    discount_type: DiscountType | None = Field(
        None,
        description="The type of discount applied to the price, if any. "
        "If no discount is applied, this should be set to None.",
    )
    with_vat: bool = Field(
        True,
        description="True if the price includes VAT (Value Added Tax), false otherwise.",
    )


class LabelPrice(BaseModel):
    """One of the price displayed on a price tag.

    For raw products (without barcode), if the price is indicated per weight
    but is not per kilogram (example: per 100g or per 500g), the price per
    kilogram should be calculated.
    """

    price: float = Field(..., description="Price in the local currency")
    with_vat: bool = Field(
        True,
        description="True if the price includes VAT (Value Added Tax), false otherwise. "
        "If there are no VAT in the country, set to false. In most cases, this should be set to true.",
    )
    currency: str | None = Field(
        ...,
        description="Currency of the price. Set to null if unknown. Examples: 'EUR', 'USD', 'GBP'",
    )
    price_per: Unit = Field(..., description="Unit of the price")
    price_is_discounted: bool = Field(
        False, description="true if the price is discounted, false otherwise"
    )
    discount_type: DiscountType = Field(
        DiscountType.NO_DISCOUNT,
        description="The type of discount applied to the price, if any. "
        "If no discount is applied, this should be set to NO_DISCOUNT.",
    )


# The schema version must be changed every time we introduce a breaking change
# in the Label model.
LABEL_SCHEMA_VERSION = "2.0"


class Label(BaseModel):
    """A label (also called price tag) indicates in a store the price of the
    product and possibly other information such as the category, price per kg,
    origin, etc.

    We distinguish between two types of labels:

    - Labels for packaged products, with barcode (type: PRODUCT): these are
    products that have a barcode, which is usually displayed on the price tag.
    For this type of label, the category should be set to NO_CATEGORY, the
    origin should be set to NO_ORIGIN.
    - Raw products, without barcode (type: CATEGORY): these are usually fruits
    and vegetables, but it can also be any product sold per weight (kg, 100g,
    etc.). For this type of label, the category should be set to the
    corresponding RawCategory, the origin should be set to the country of
    origin of the product (if indicated) and the barcode should be empty.
    """

    type: Literal["PRODUCT", "CATEGORY"] = Field(
        ...,
        description="The type of product the label is referring to. It should be "
        "`PRODUCT` for packaged products with barcode, and `CATEGORY` for raw "
        "products without barcode.",
    )
    category: RawCategory | None = Field(
        None,
        description="The category of the product. "
        "If type=PRODUCT, this should be set to the null.",
    )  # category_tag
    prices: list[LabelPrice] = Field(
        ...,
        description="All prices found on the label. Depending on the type of "
        "price tag, there can be multiple prices displayed. "
        "For packaged products (type=PRODUCT), the price per unit is the most common one. "
        "The price per kg is also often included as well. "
        "For raw products (type=CATEGORY), the price per kg is the most common one. "
        "There can also be a discount applied to the price. In such case, both "
        "the original price and the discounted price should be included in the list.",
    )
    origin: Origin | None = Field(
        ...,
        description="The country of origin of the product. "
        "If type=PRODUCT, this should be set to null. If type=CATEGORY, this should "
        "be set to the country of origin of the product, such as France, Italy, Spain, etc.",
    )
    organic: bool = Field(
        ...,
        description="true if the product is organic, false otherwise. If true, "
        "there should be evidence on the label suggesting that the product is "
        "organic, such as the EU organic logo.",
    )
    barcode: str = Field(
        ...,
        description="The barcode of the product, if available. "
        "The barcode are usually numbers with 13 (EAN13) or 8 (EAN8) digits. You should "
        "*NOT* try to decode the barcode stripe (also called modules), but use the "
        "barcode number displayed on the label. "
        "If type=CATEGORY, this should be empty.",
    )
    product_name: str = Field(
        ...,
        description="The name of the product, as displayed on the label. "
        "For raw products (type=CATEGORY), this is usually the name of the fruit or vegetable. "
        "For products with barcode (type=PRODUCT), it usually includes the brand, a short "
        "description of the product, and eventually the quantity. "
        "examples: 'NOCCIOLATA BIO 650G', 'Simpson Donuts', 'GERBLE BISCUIT PIST ABRICOT160G', "
        "'Radis Blanc', 'Concombre lisse', 'Courget Butternut', 'Tomatoes', 'Organic Bananas'",
    )
    blurriness: float = Field(
        0.0,
        description="The blurriness of the label image, from 0.0 (not blurry) to 1.0 (very blurry).",
        ge=0.0,
        le=1.0,
    )
    truncated: bool = Field(
        False,
        description="true if the photo of the price tag is truncated, false otherwise. A photo of a price tag is considered truncated if any of these occurs:\n"
        "- the barcode (for packaged products) or the product name (for raw products) is not fully visible on the photo\n"
        "- the price is not fully visible on the photo\n",
    )
    is_price_tag: bool = Field(
        True,
        description="true if the image is a price tag, false otherwise. If the image seems to come from a receipt or a catalogue, this should be set to false.",
    )

    @computed_field
    @property
    def selected_price(self) -> SelectedPrice | None:
        """From all individual price reference on the price tag, construct a
        Price ready to be added to Open Prices.

        In case
        """
        if not self.prices:
            return None

        # sort prices to have prices with VAT first
        sorted_prices = sorted(self.prices, key=lambda p: p.with_vat, reverse=True)

        price_grouped_by_per: dict[Unit, list[LabelPrice]] = {unit: [] for unit in Unit}
        for price in sorted_prices:
            # Convert price_per to Unit.KILOGRAM if it is LITER
            price_per = (
                price.price_per if price.price_per != Unit.LITER else Unit.KILOGRAM
            )
            price_grouped_by_per[price_per].append(price)

        if self.type == "CATEGORY":
            # We first consider the price per KILOGRAM for raw products then
            # per UNIT
            selected_units = [Unit.KILOGRAM, Unit.UNIT]
        else:
            # We only consider the price per UNIT for packaged products.
            selected_units = [Unit.UNIT]

        for selected_unit in selected_units:
            prices_per_selected_unit = price_grouped_by_per[selected_unit]
            # Get the first occurence of a price with the selected unit and
            # without discount. If there are one price with VAT and one without
            # VAT, we take the one with VAT (thanks to sorting).
            no_discount_price = next(
                (
                    p
                    for p in prices_per_selected_unit
                    if p.discount_type is DiscountType.NO_DISCOUNT
                ),
                None,
            )
            discounted_price = next(
                (
                    p
                    for p in prices_per_selected_unit
                    # We only consider the discount types SALE and SEASONAL as
                    # these are the only ones that applies to any client.
                    if p.discount_type in (DiscountType.SALE, DiscountType.SEASONAL)
                ),
                None,
            )
            if discounted_price:
                # There is a discounted price displayed on the price tag.

                # We search again for a price without discount, but with the
                # same VAT status as the discounted price (otherwise the two
                # prices cannot be compared).
                no_discount_price = next(
                    (
                        p
                        for p in prices_per_selected_unit
                        if p.discount_type is DiscountType.NO_DISCOUNT
                        and p.with_vat == discounted_price.with_vat
                    ),
                    None,
                )
                return SelectedPrice(
                    price=discounted_price.price,
                    with_vat=discounted_price.with_vat,
                    currency=discounted_price.currency,
                    price_per=selected_unit,
                    price_is_discounted=True,
                    # If we didn't find a price without discount, we set the
                    # price_without_discount to null (as it's unknown).
                    price_without_discount=(
                        no_discount_price.price if no_discount_price else None
                    ),
                    discount_type=discounted_price.discount_type,
                )
            elif no_discount_price:
                # This is a regular price, without discount
                return SelectedPrice(
                    price=no_discount_price.price,
                    with_vat=no_discount_price.with_vat,
                    currency=no_discount_price.currency,
                    price_per=selected_unit,
                    price_is_discounted=False,
                    price_without_discount=None,
                    # discount_type must be null if price_is_discounted is False
                    discount_type=None,
                )

        return None


class BarcodeSimilarityMatch(BaseModel):
    barcode: str = Field(..., description="The similar barcode")
    distance: int = Field(
        ..., description="The Levenshtein distance between the two barcodes."
    )


class LabelWithSimilarBarcodes(Label):
    """This class extends the Label class with a list of similar barcodes.

    Extraction of barcode using Gemini sometimes produces incorrect results,
    as the image is often blurry or the barcode is partially occluded.
    To help the user find the correct barcode, we use a fuzzy search to find
    barcodes that are similar to the extracted barcode. The similar barcodes
    are sorted by increasing Levenshtein distance.
    """

    raw_barcode: str = Field(
        ..., description="The raw extracted barcode, before normalization."
    )
    similar_barcodes: list[BarcodeSimilarityMatch] = Field(
        [],
        description="A list of suggested barcodes for the product, if any. "
        "The suggestions are based on a fuzzy search of barcodes that are similar "
        "to the extracted barcode. The list is sorted by increasing Levenshtein distance.",
    )


def preprocess_price_tag(image: Image.Image) -> Image.Image:
    # Gemini model max payload size is 20MB
    # To prevent the payload from being too large, we resize the images
    max_size = 1024
    if image.width > max_size or image.height > max_size:
        image = image.copy()
        image.thumbnail((max_size, max_size))
    return image


EXTRACT_PRICE_TAG_PROMPT = (
    "Here is one picture containing a price label, extract information "
    "from it. If you cannot decode an attribute, set it to an empty string."
)


def extract_from_price_tag(
    image: Image.Image,
) -> common_google.types.GenerateContentResponse:
    """Extract price tag information from an image.

    :param image: the input Pillow image. Image preprocessing is done
        automatically to resize the image if it is too large.
    :return: the Gemini response
    """
    preprocessed_image = preprocess_price_tag(image)

    with genai.Client(
        credentials=common_google.get_google_credentials(),
        project=settings.GOOGLE_PROJECT,
    ) as client:
        return client.models.generate_content(
            model=common_google.GEMINI_MODEL_VERSION,
            contents=[
                EXTRACT_PRICE_TAG_PROMPT,
                preprocessed_image,
            ],
            config=common_google.get_generation_config(Label, thinking_level="minimal"),
        )


async def extract_from_price_tag_async(
    client: genai.client.AsyncClient, image: Image.Image
) -> common_google.types.GenerateContentResponse:
    """Asynchronous version of extract_from_price_tag.

    Image preprocessing (resizing to maximum size) must be done before calling
    this function.

    :param client: the AsyncClient instance to use for the request.
    :param image: the input Pillow image, already preprocessed.
    :return: the Gemini response
    """
    response = await client.models.generate_content(
        model=common_google.GEMINI_MODEL_VERSION,
        contents=[
            EXTRACT_PRICE_TAG_PROMPT,
            image,
        ],
        config=common_google.get_generation_config(Label, thinking_level="minimal"),
    )
    return response


async def extract_from_price_tag_batch(
    images: list[Image.Image],
) -> list[common_google.types.GenerateContentResponse]:
    """Extract price tag information from a batch of images.

    This function processes multiple images in parallel using asyncio.

    :param images: a list of Pillow images, already preprocessed (resized).
    :return: a list of Gemini responses, one for each image
    """
    async with genai.Client(
        credentials=common_google.get_google_credentials(),
        project=settings.GOOGLE_PROJECT,
    ).aio as aclient:
        tasks = [extract_from_price_tag_async(aclient, image) for image in images]
        return await asyncio.gather(*tasks)


# We use async_to_sync to make the function synchronous for compatibility
# with the rest of the codebase that expects synchronous functions.
# See
# https://docs.djangoproject.com/en/5.2/topics/async/#async-adapter-functions
sync_extract_from_price_tag_batch = async_to_sync(extract_from_price_tag_batch)


def detect_price_tags(
    image: Image.Image,
    model_name: str = PRICE_TAG_DETECTOR_MODEL_NAME,
    model_version: str = PRICE_TAG_DETECTOR_TRITON_VERSION,
    label_names: list[str] = PRICE_TAG_DETECTOR_LABEL_NAMES,
    image_size: int = PRICE_TAG_DETECTOR_IMAGE_SIZE,
    triton_uri: str = settings.TRITON_URI,
    threshold: float = 0.25,
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
    :param threshold: the detection threshold, defaults to 0.25
    :return: the detection results
    """
    detector = ObjectDetector(
        model_name=model_name,
        label_names=label_names,
        image_size=image_size,
    )
    # The object detector expects a numpy array as input
    image_array = np.asarray(image.convert("RGB"))
    return detector.detect_from_image(
        image_array,
        triton_uri=triton_uri,
        threshold=threshold,
        model_version=model_version,
    )


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

    predictions = []
    preprocessed_images = []
    for price_tag in price_tags:
        cropped_image = crop_image(proof.file_path_full, price_tag.bounding_box)
        preprocessed_images.append(preprocess_price_tag(cropped_image))

    # Sending requests in parallel using asyncio was responsible to network
    # exceptions in production, so we added here a setting to control
    # whether to use async requests or not.
    # See https://github.com/openfoodfacts/open-prices/issues/893
    if settings.PRICE_TAG_EXTRACTION_ASYNC_REQUESTS:
        # We send requests to Gemini in parallel using asyncio
        # to speed up the extraction process.
        responses = sync_extract_from_price_tag_batch(preprocessed_images)
    else:
        responses = [extract_from_price_tag(image) for image in preprocessed_images]
    for price_tag, response in zip(price_tags, responses, strict=False):
        if response.parsed is None:
            logger.info(
                "Failed to extract price tag for price tag id %s: %s",
                price_tag.id,
                response.text,
            )
            continue

        # barcode post-processing
        # 1) fix barcode with some custom rules
        # 2) if the barcode is still unknown, generate similar barcodes
        barcode = response.parsed.barcode
        raw_barcode = barcode
        similar_barcodes = []
        # 1) barcode fix
        if barcode:
            # only fix barcodes that are not valid
            if len(barcode) < 13 and not common_openfoodfacts.barcode_is_valid(barcode):
                # in the USA, some barcodes are not "complete"
                if proof.currency == "USD":
                    barcode = common_openfoodfacts.barcode_fix_short_codes_from_usa(
                        barcode
                    )
            # normalize barcode
            barcode = normalize_barcode(barcode)

        # barcode similarity search is quite costly (500~1000ms for 4M
        # products), so we only run it if the barcode doesn't exist in the
        # database
        if barcode and not Product.objects.filter(code=barcode).exists():
            # Only return products with a levenshtein distance between 1 and 3
            # Don't return too many results
            similar_barcodes_qs = Product.objects.fuzzy_barcode_search(
                barcode, max_distance=3, limit=10
            )
            similar_barcodes = [
                BarcodeSimilarityMatch(barcode=p.code, distance=p.distance)
                for p in similar_barcodes_qs
                # Check that barcode is valid (correct check digit)
                if common_openfoodfacts.barcode_is_valid(p.code)
            ]

        data = LabelWithSimilarBarcodes(
            **{**dict(response.parsed), "barcode": barcode},  # merge any barcode fix
            raw_barcode=raw_barcode,
            similar_barcodes=similar_barcodes,
        )
        try:
            prediction = PriceTagPrediction.objects.create(
                price_tag=price_tag,
                type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
                model_name=common_google.GEMINI_MODEL_NAME,
                model_version=common_google.GEMINI_MODEL_VERSION,
                schema_version=LABEL_SCHEMA_VERSION,
                data=data.model_dump(),
                thought_tokens=common_google.extract_thought_tokens(response),
            )
            predictions.append(prediction)
        except Exception as e:
            logger.exception(e)

    return predictions


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


def update_price_tag_extraction(price_tag_id: int) -> PriceTagPrediction | None:
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
        return None

    price_tag_prediction = PriceTagPrediction.objects.filter(
        price_tag=price_tag, type=proof_constants.PRICE_TAG_EXTRACTION_TYPE
    ).first()

    if not price_tag_prediction:
        logger.info(
            "Price tag %s does not have a price tag extraction prediction",
            price_tag.id,
        )
        return None

    cropped_image = crop_image(proof.file_path_full, price_tag.bounding_box)
    gemini_response = extract_from_price_tag(cropped_image)
    price_tag_prediction.model_name = common_google.GEMINI_MODEL_NAME
    price_tag_prediction.model_version = common_google.GEMINI_MODEL_VERSION
    price_tag_prediction.schema_version = LABEL_SCHEMA_VERSION
    price_tag_prediction.data = gemini_response.parsed.model_dump()
    price_tag_prediction.thought_tokens = common_google.extract_thought_tokens(
        gemini_response
    )
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
                proof_prediction=proof_prediction,
                bounding_box=detected_object["bounding_box"],
                status=None,
                created_by=None,
                updated_by=None,
            )
            created.append(price_tag)

    if run_extraction:
        run_and_save_price_tag_extraction(created, proof)

    return created


def run_and_save_price_tag_detection(
    image: Image.Image,
    proof: Proof,
    overwrite: bool = False,
    run_extraction: bool = True,
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
    if proof.type != proof_constants.TYPE_PRICE_TAG:
        logger.debug("Skipping proof %s, not of type PRICE_TAG", proof.id)
        return None

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
        type=proof_constants.PROOF_PREDICTION_OBJECT_DETECTION_TYPE,
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


def price_tag_prediction_has_predicted_barcode_valid(
    price_tag_prediction: PriceTagPrediction,
) -> bool:
    """
    proof_constants.PRICE_TAG_PREDICTION_TAG_BARCODE_VALID
    Differences between schema versions: No
    """
    if price_tag_prediction.data.get("barcode"):
        barcode = price_tag_prediction.data.get("barcode")
        if common_openfoodfacts.barcode_is_valid(barcode):
            return True
    return False


def price_tag_prediction_has_predicted_product_exists(
    price_tag_prediction: PriceTagPrediction,
) -> bool:
    """
    proof_constants.PRICE_TAG_PREDICTION_TAG_PRODUCT_EXISTS
    Differences between schema versions: No
    """
    from open_prices.products.models import Product

    if price_tag_prediction.data.get("barcode"):
        barcode = price_tag_prediction.data.get("barcode")
        if Product.objects.filter(code=barcode).exists():
            return True
    return False


def price_tag_prediction_has_predicted_category_tag_valid(
    price_tag_prediction: PriceTagPrediction,
) -> bool:
    """
    proof_constants.PRICE_TAG_PREDICTION_TAG_CATEGORY_TAG_VALID
    Differences between schema versions:
    - schema v1: category_tag is stored in data['product']
    - schema v2: category_tag is stored in data['category']
    """
    if price_tag_prediction.schema_version == "1.0":
        if price_tag_prediction.data.get("product"):
            category_tag = price_tag_prediction.data.get("product")
            if category_tag.startswith("en:"):
                return True
    elif price_tag_prediction.schema_version == "2.0":
        if price_tag_prediction.data.get("category"):
            category_tag = price_tag_prediction.data.get("category")
            if category_tag.startswith("en:"):
                return True
    return False
