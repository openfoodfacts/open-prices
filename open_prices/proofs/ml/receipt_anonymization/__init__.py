import logging
import typing

import numpy as np
from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.capabilities import Thinking
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml.receipt_anonymization.ocr import Word, run_ocr
from open_prices.proofs.models import Proof, ProofPrediction
from open_prices.proofs.utils import (
    convert_image,
    generate_image_thumbnail_cv2,
    open_image_cv2,
)

logger = logging.getLogger(__name__)


class PersonalInfo(BaseModel):
    type: str = Field(
        description="the type of personal information detected. Possible values are: 'name' (for cashier or buyer name) and 'fidelity_card_id' (for fidelity card ID).",
        json_schema_extra={"enum": ["name", "fidelity_card_id"]},
    )
    value: str = Field(
        description="the value of the personal information detected. Examples: 'John Doe', '14:30', '1234567890'"
    )


class PersonalInfoList(BaseModel):
    items: list[PersonalInfo] = Field(
        description="a list of personal information detected in the receipt. If no personal information was found, items must be an empty list."
    )


INSTRUCTIONS = """Identify the following personal information from this receipt:
- name of the supermarket cashier, if any. It should only be included in the results if the first name and/or last name of the cashier is mentioned.
- name of the buyer (who may have used a fidelity card). Some street names may contain name of people (as the address of the shop is often displayed on the receipt), but they should not be included in the results.
- fidelity card ID

For the value:
- don't change the formatting, keep the value as it is displayed on the receipt.
- only include the personal information, not the suffix (ex: don't include 'fidelity card ID:', but only the ID).
"""


def get_pydantic_ai_model(name: str):
    """Return an OpenAI chat model instance for the given model name.

    This function can be mocked in tests to return TestModel.
    """
    return OpenAIChatModel(
        name,
        # OPENAI_API_KEY and OPENAI_BASE_URL are automatically picked up
        provider=OpenAIProvider(),
    )


def extract_personal_info(
    image: np.ndarray, model: str, max_size: int = 1200
) -> PersonalInfoList:
    """Extract personal information from a receipt image or URL.

    :params image: The receipt image as a NumPy array (OpenCV, BGR).
    :params max_size: The maximum size of the image to process. If the image is larger
        than this, it will be resized to fit within these dimensions.
    :params model: The model to use for extracting personal information.
    """
    # Resize to max size
    image = generate_image_thumbnail_cv2(image, max_size)
    image_bytes = convert_image(image, format="jpeg")
    image_content = BinaryContent(data=image_bytes, media_type="image/jpeg")
    user_prompt = [INSTRUCTIONS, image_content]
    agent = Agent(
        model=get_pydantic_ai_model(model),
        output_type=PersonalInfoList,
        # Thinking effort set to minimal gives good results,
        # let's keep it this way for now
        capabilities=[Thinking(effort="minimal")],
    )
    result = agent.run_sync(user_prompt)
    return typing.cast(PersonalInfoList, result.output)


def add_margin_bounding_box(
    word: Word,
    left_margin: float = 0.0,
    right_margin: float = 0.0,
) -> None:
    """Adds horizontal margin to the bounding box of a word.

    PaddleOCR often returns bounding boxes that don't cover the entire word,
    so we add margin to the bounding box. Each value (left_margin, right_margin)
    is a fraction of the width of the bounding box, so it can be adjusted to
    fit the word.

    If the word is a single character, we add extra left-margin to fit the character
    (x2.5 multiplier).
    """
    x_min, y_min, x_max, y_max = word.bounding_box
    text_len = len(word.text)
    box_width = x_max - x_min
    # Special case for single-character words: add extra left-margin to fit the character
    if text_len == 1:
        left_margin *= 2.5
    x_min -= left_margin * box_width / text_len
    x_max += right_margin * box_width / text_len
    word.bounding_box = (
        max(x_min, 0.0),
        y_min,
        min(x_max, 1.0),
        y_max,
    )


class AnonymizationResult(BaseModel):
    words: list[Word]


def anonymize_receipt(
    image: np.ndarray,
    model: str,
    max_size: int = 1200,
    add_margin: bool = True,
) -> AnonymizationResult:
    """Detect personal information in the receipt image and anonymize it by adding
    black boxes over the detected personal information.

    :param image: The receipt image as a NumPy array (OpenCV format, BGR).
    :param model: The LLM to use for detecting personal information.
    :param max_size: The maximum size of the image to process.
    :param add_margin: Whether to add horizontal margin to the bounding box of
        detected personal information. PaddleX often return word bounding box that are
        too tight, this parameter controls whether to add margin to the bounding box.
    """
    personal_info_list = extract_personal_info(image, model=model, max_size=max_size)
    ocr_result = run_ocr(image=image, max_size=max_size)

    pii_words = []
    for item in personal_info_list.items:
        value = item.value
        pattern = value.split(" ")
        words = ocr_result.locate_words(pattern)
        if words:
            for word in words:
                if add_margin:
                    add_margin_bounding_box(
                        word,
                        left_margin=1,
                        right_margin=0.4,
                    )
                pii_words.append(word)
    return AnonymizationResult(words=pii_words)


def run_and_save_receipt_anonymization_prediction(
    image: np.ndarray | None,
    proof: Proof,
    overwrite: bool = False,
    model: str = "minimax/minimax-m3",
) -> ProofPrediction | None:
    """Run receipt anonymization pipeline and save the prediction in
    ProofPrediction table.

    :param image: the image to run the model on, as a numpy array (uint8, in BGR
        format).
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
        proof=proof,
        type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
    ).exists():
        if overwrite:
            logger.info(
                "Overwriting existing anonymization prediction for proof %s", proof.id
            )
            ProofPrediction.objects.filter(
                proof=proof,
                type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
            ).delete()
        else:
            logger.debug(
                "Proof %s already has an anonymization prediction",
                proof.id,
            )
            return None

    if image is None:
        image = open_image_cv2(proof.file_path_full)
    # prediction may be None if the model failed to extract
    try:
        anonymization_result = anonymize_receipt(image, model=model)
    except Exception:
        logger.exception("Receipt anonymization failed")
        return None

    proof.refresh_from_db(fields=["draft"])
    if proof.draft is False:
        logger.info(
            "Proof is not a draft: it was probably finalized before prediction "
            "was ready. The receipt anonymization prediction will not be saved."
        )
        return None

    try:
        return ProofPrediction.objects.create(
            proof=proof,
            type=proof_constants.PROOF_PREDICTION_RECEIPT_ANONYMIZATION_TYPE,
            model_name=model,
            model_version=model,
            data=anonymization_result.model_dump(),
        )
    except Exception as e:
        logger.exception(e)
    return None
