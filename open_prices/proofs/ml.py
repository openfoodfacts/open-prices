"""
Proof ML/AI
- predict Proof type with triton
- detect Proof's PriceTags with triton
- extract data from PriceTags with Gemini
"""

import asyncio
import base64
import enum
import gzip
import json
import logging
import time
from pathlib import Path
from typing import Any, Literal

import typing_extensions as typing
from asgiref.sync import async_to_sync
from django.conf import settings
from google import genai
from openfoodfacts.ml.image_classification import ImageClassifier
from openfoodfacts.ml.object_detection import ObjectDetectionRawResult, ObjectDetector
from openfoodfacts.utils import http_session
from PIL import Image
from pydantic import BaseModel, Field, computed_field

from open_prices.common import google as common_google
from open_prices.proofs import constants as proof_constants
from open_prices.proofs.models import (
    PriceTag,
    PriceTagPrediction,
    Proof,
    ProofPrediction,
    ReceiptItem,
)

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


# TODO: what about other categories?
# We keep the Products here for now to keep the compatibility with the
# ReceiptItem model
class Products(enum.Enum):
    OTHER = "other"
    APPLES = "en:apples"
    APRICOTS = "en:apricots"
    ARTICHOKES = "en:artichokes"
    ASPARAGUS = "en:asparagus"
    AUBERGINES = "en:aubergines"
    AVOCADOS = "en:avocados"
    BANANAS = "en:bananas"
    BEETROOT = "en:beetroot"
    BERRIES = "en:berries"
    BLACKBERRIES = "en:blackberries"
    BLUEBERRIES = "en:blueberries"
    BOK_CHOY = "en:bok-choy"
    BROCCOLI = "en:broccoli"
    CABBAGES = "en:cabbages"
    CARROTS = "en:carrots"
    CAULIFLOWERS = "en:cauliflowers"
    CELERY = "en:celery"
    CELERIAC = "en:celeriac"
    CELERY_STALK = "en:celery-stalk"
    CEP_MUSHROOMS = "en:cep-mushrooms"
    CHANTERELLES = "en:chanterelles"
    CHARDS = "en:chards"
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
    FENNEL_BULBS = "en:fennel-bulbs"
    FIGS = "en:figs"
    GARLIC = "en:garlic"
    GINGER = "en:ginger"
    GRAPEFRUITS = "en:grapefruits"
    GRAPES = "en:grapes"
    GREEN_BEANS = "en:green-beans"
    GREEN_SWEET_PEPPERS = "en:green-sweet-peppers"
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
    PARSNIP = "en:parsnip"
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
    RED_BELL_PEPPERS = "en:red-bell-peppers"
    RED_ONIONS = "en:red-onions"
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
    YELLOW_ONIONS = "en:yellow-onions"
    ZUCCHINI = "en:zucchini"


class RawCategory(enum.StrEnum):
    APPLES = "en:apples"
    APRICOTS = "en:apricots"
    ARTICHOKES = "en:artichokes"
    ASPARAGUS = "en:asparagus"
    AUBERGINES = "en:aubergines"
    AVOCADOS = "en:avocados"
    BANANAS = "en:bananas"
    BEETROOT = "en:beetroot"
    BERRIES = "en:berries"
    BLACKBERRIES = "en:blackberries"
    BLUEBERRIES = "en:blueberries"
    BOK_CHOY = "en:bok-choy"
    BROCCOLI = "en:broccoli"
    CABBAGES = "en:cabbages"
    CARROTS = "en:carrots"
    CAULIFLOWERS = "en:cauliflowers"
    CELERY = "en:celery"
    CELERIAC = "en:celeriac"
    CELERY_STALK = "en:celery-stalk"
    CEP_MUSHROOMS = "en:cep-mushrooms"
    CHANTERELLES = "en:chanterelles"
    CHARDS = "en:chards"
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
    FENNEL_BULBS = "en:fennel-bulbs"
    FIGS = "en:figs"
    GARLIC = "en:garlic"
    GINGER = "en:ginger"
    GRAPEFRUITS = "en:grapefruits"
    GRAPES = "en:grapes"
    GREEN_BEANS = "en:green-beans"
    GREEN_SWEET_PEPPERS = "en:green-sweet-peppers"
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
    PARSNIP = "en:parsnip"
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
    RED_BELL_PEPPERS = "en:red-bell-peppers"
    RED_ONIONS = "en:red-onions"
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
    YELLOW_ONIONS = "en:yellow-onions"
    ZUCCHINI = "en:zucchini"
    OTHER = "other"


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


class Unit(enum.StrEnum):
    KILOGRAM = "KILOGRAM"
    LITER = "LITER"
    UNIT = "UNIT"


class DiscountType(enum.StrEnum):
    QUANTITY = "QUANTITY"  # example: buy 1 get 1 free
    SALE = "SALE"  # example: 50% off
    SEASONAL = "SEASONAL"  # example: Christmas sale
    LOYALTY_PROGRAM = "LOYALTY_PROGRAM"  # example: 10% off for members
    EXPIRES_SOON = "EXPIRES_SOON"  # example: 30% off expiring soon
    PICK_IT_YOURSELF = "PICK_IT_YOURSELF"  # example: 5% off for pick-up
    SECOND_HAND = "SECOND_HAND"  # example: second hand books or clothes
    OTHER = "OTHER"
    NO_DISCOUNT = "NO_DISCOUNT"  # no discount applied


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

        price_grouped_by_per = {unit: [] for unit in Unit}
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
                    discount_type=DiscountType.NO_DISCOUNT,
                )

        return None


class ReceiptItemType(typing.TypedDict):
    product: Products
    price: float
    product_name: str


class Receipt(typing.TypedDict):
    store_name: str
    store_address: str
    store_city_name: str
    date: str
    # currency: str
    # price_count: int
    # price_total: float
    items: list[ReceiptItemType]


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
    image: Image.Image, thinking_budget: int = -1
) -> common_google.types.GenerateContentResponse:
    """Extract price tag information from an image.

    :param image: the input Pillow image. Image preprocessing is done
        automatically to resize the image if it is too large.
    :param thinking_budget: the thinking budget for the Gemini model, in
        tokens. 0 is DISABLED. -1 is AUTOMATIC.
    :return: the Gemini response
    """
    client = common_google.get_genai_client()
    preprocessed_image = preprocess_price_tag(image)

    response = client.models.generate_content(
        model=common_google.GEMINI_MODEL_VERSION,
        contents=[
            EXTRACT_PRICE_TAG_PROMPT,
            preprocessed_image,
        ],
        config=common_google.get_generation_config(
            Label, thinking_budget=thinking_budget
        ),
    )
    return response


async def extract_from_price_tag_async(
    client: genai.Client, image: Image.Image, thinking_budget: int = -1
) -> common_google.types.GenerateContentResponse:
    """Asynchronous version of extract_from_price_tag.

    Image preprocessing (resizing to maximum size) must be done before calling
    this function.

    :param client: the genai.Client instance to use for the request.
    :param image: the input Pillow image, already preprocessed.
    :param thinking_budget: the thinking budget for the Gemini model, in
        tokens. 0 is DISABLED. -1 is AUTOMATIC.
    :return: the Gemini response
    """
    response = await client.aio.models.generate_content(
        model=common_google.GEMINI_MODEL_VERSION,
        contents=[
            EXTRACT_PRICE_TAG_PROMPT,
            image,
        ],
        config=common_google.get_generation_config(
            Label, thinking_budget=thinking_budget
        ),
    )
    return response


async def extract_from_price_tag_batch(
    images: list[Image.Image], thinking_budget: int = -1
) -> list[common_google.types.GenerateContentResponse]:
    """Extract price tag information from a batch of images.

    This function processes multiple images in parallel using asyncio.

    :param images: a list of Pillow images, already preprocessed (resized).
    :param thinking_budget: the thinking budget for the Gemini model, in
        tokens. 0 is DISABLED. -1 is AUTOMATIC.
    :return: a list of Gemini responses, one for each image
    """
    responses = []
    # We get the uncached version of the client because otherwise
    # the event loop configuration done during the client initialization
    # leads to an exception when reusing the client in an async context
    # (due to the event loop being closed)
    client = common_google.get_genai_client.__wrapped__()
    tasks = [
        extract_from_price_tag_async(client, image, thinking_budget=thinking_budget)
        for image in images
    ]
    responses = await asyncio.gather(*tasks)
    return responses


# We use async_to_sync to make the function synchronous for compatibility
# with the rest of the codebase that expects synchronous functions.
# See
# https://docs.djangoproject.com/en/5.2/topics/async/#async-adapter-functions
sync_extract_from_price_tag_batch = async_to_sync(extract_from_price_tag_batch)


def extract_from_receipt(image: Image.Image) -> Receipt:
    """Extract receipt information from an image."""
    # Gemini model max payload size is 20MB
    # To prevent the payload from being too large, we resize the images before
    # upload
    max_size = 1024
    if image.width > max_size or image.height > max_size:
        image = image.copy()
        image.thumbnail((max_size, max_size))

    prompt = "Extract all relevent information, use empty strings for unknown values."
    client = common_google.get_genai_client()
    response = client.models.generate_content(
        model=common_google.GEMINI_MODEL_VERSION,
        contents=[
            prompt,
            image,
        ],
        config=common_google.get_generation_config(Receipt),
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


def run_ocr_on_image(image_path: Path | str, api_key: str) -> dict[str, Any] | None:
    """Run Google Cloud Vision OCR on the image stored at the given path.

    :param image_path: the path to the image
    :param api_key: the Google Cloud Vision API key
    :return: the OCR data as a dict or None if an error occurred

    This is similar to the run_ocr.py script in openfoodfacts-server:
    https://github.com/openfoodfacts/openfoodfacts-server/blob/main/scripts/run_ocr.py
    """
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    base64_content = base64.b64encode(image_bytes).decode("utf-8")
    url = f"{common_google.GOOGLE_CLOUD_VISION_OCR_API_URL}?key={api_key}"
    data = {
        "requests": [
            {
                "features": [
                    {"type": feature}
                    for feature in common_google.GOOGLE_CLOUD_VISION_OCR_FEATURES
                ],
                "image": {"content": base64_content},
            }
        ]
    }
    response = http_session.post(url, json=data)

    if not response.ok:
        logger.debug(
            "Error running OCR on image %s, HTTP %s\n%s",
            image_path,
            response.status_code,
            response.text,
        )
    return response.json()


def fetch_and_save_ocr_data(image_path: Path | str, override: bool = False) -> bool:
    """Run OCR on the image stored at the given path and save the result to a
    JSON file.

    The JSON file will be saved in the same directory as the image, with the
    same name but a `.json` extension.

    :param image_path: the path to the image
    :param override: whether to override existing OCR data, default to False
    :return: True if the OCR data was saved, False otherwise
    """
    image_path = Path(image_path)

    if image_path.suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        logger.debug("Skipping %s, not a supported image type", image_path)
        return False

    if not settings.GOOGLE_CLOUD_VISION_API_KEY:
        logger.error("No Google Cloud Vision API key found")
        return False

    ocr_json_path = image_path.with_suffix(".json.gz")

    if ocr_json_path.exists() and not override:
        logger.info("OCR data already exists for %s", image_path)
        return False

    data = run_ocr_on_image(image_path, settings.GOOGLE_CLOUD_VISION_API_KEY)

    if data is None:
        return False

    data["created_at"] = int(time.time())

    with gzip.open(ocr_json_path, "wt") as f:
        f.write(json.dumps(data))

    logger.debug("OCR data saved to %s", ocr_json_path)
    return True


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

    predictions = []
    preprocessed_images = []
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
        preprocessed_images.append(preprocess_price_tag(cropped_image))

    # We send requests to Gemini in parallel using asyncio
    # to speed up the extraction process.
    responses = sync_extract_from_price_tag_batch(
        preprocessed_images, thinking_budget=-1
    )
    for price_tag, response in zip(price_tags, responses):
        try:
            prediction = PriceTagPrediction.objects.create(
                price_tag=price_tag,
                type=proof_constants.PRICE_TAG_EXTRACTION_TYPE,
                model_name=common_google.GEMINI_MODEL_NAME,
                model_version=common_google.GEMINI_MODEL_VERSION,
                schema_version=LABEL_SCHEMA_VERSION,
                data=response.parsed.model_dump(),
                thought_tokens=common_google.extract_thought_tokens(response),
            )
            predictions.append(prediction)
        except Exception as e:
            logger.exception(e)

    return predictions


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
        return []

    price_tag_prediction = PriceTagPrediction.objects.filter(
        price_tag=price_tag, type=proof_constants.PRICE_TAG_EXTRACTION_TYPE
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


def create_receipt_items_from_proof_prediction(
    proof: Proof, proof_prediction: ProofPrediction
) -> list[ReceiptItem]:
    """Create receipt items from a proof prediction containing receipt item
    detections."""

    if proof_prediction.model_name != common_google.GEMINI_MODEL_NAME:
        logger.error(
            "Proof prediction model %s is not a receipt extraction",
            proof_prediction.model_name,
        )
        return []

    created = []
    for index, predicted_item in enumerate(proof_prediction.data["items"]):
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


def run_and_save_receipt_extraction_prediction(
    image: Image, proof: Proof, overwrite: bool = False
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
            data=prediction,
        )
        create_receipt_items_from_proof_prediction(proof, proof_prediction)
        return proof_prediction
    except Exception as e:
        logger.exception(e)


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

    :param proof_id: the ID of the proof to be classified
    :param run_price_tag_extraction: whether to run the price tag extraction
        model on the detected price tags, defaults to True
    """
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
    if run_receipt_extraction:
        run_and_save_receipt_extraction_prediction(image, proof)
