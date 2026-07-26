"""PaddleOCR utilities for receipt anonymization."""

from base64 import b64encode

import numpy as np
import requests
from django.conf import settings
from pydantic import BaseModel, field_validator

from open_prices.proofs.ml.receipt_anonymization.paddle import PaddleXOcrResponse
from open_prices.proofs.utils import convert_image, generate_image_thumbnail_cv2


class Word(BaseModel):
    """A single word detected by PaddleOCR.

    Attributes:
        text (str): The text of the word.
        bounding_box (tuple[float, float, float, float]): The relative coordinates of the bounding box of the word, as a tuple of (x_min, y_min, x_max, y_max).
        line_idx (int | None): The index of the line the word belongs to.
    """

    text: str
    bounding_box: tuple[float, float, float, float]
    line_idx: int | None = None

    @field_validator("bounding_box", mode="after")
    @classmethod
    def validate_bounding_box(
        cls, value: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        if not all(0 <= x <= 1 for x in value):
            raise ValueError("Bounding box coordinates must be between 0 and 1.")
        return value


def get_search_map(input_words: list[Word]) -> tuple[str, np.ndarray]:
    """Constructs a search map from the input words, mapping each character to
    its corresponding word index.

    This is used to find the location of a specific string on an image, leveraging
    Paddle OCR result. The search string is constructed by joining all non-space
    words, while the index map maps each character to its corresponding word index.

    Each word is joined *without* any separator, to maximize the chance of matching
    the search string exactly.

    Args:
        input_words (list[Word]): The list of input words.

    Returns:
        tuple[str, np.ndarray]: The search string and the index map. The index map
        is a 1D numpy array mapping each character (excluding spaces words) to its
        corresponding word index.
    """
    to_join: list[str] = []
    str_len = sum(len(w.text) for w in input_words if not w.text.isspace())
    index_map = np.zeros(str_len, dtype=int)
    offset = 0
    for word_idx, word in enumerate(input_words):
        if word.text.isspace():
            continue
        index_map[offset : offset + len(word.text)] = word_idx
        to_join.append(word.text)
        offset += len(word.text)
    search_str = "".join(to_join)
    return search_str, index_map


def locate_words(query: list[str], input_words: list[Word]) -> list[int]:
    """Match the words in `query` to the words in `input_words`, and return the
    indices of the matched words (with respect to `input_words`)."""
    search_str, index_map = get_search_map(input_words)
    pattern = "".join(query)

    latest_match_idx = -1
    word_indices = []

    while (match_idx := search_str.find(pattern, latest_match_idx + 1)) != -1:
        offset = 0
        latest_match_idx = match_idx
        for word in query:
            word_idx = index_map[match_idx + offset]
            offset += len(word)
            word_indices.append(word_idx.item())
    return word_indices


class OcrResult(BaseModel):
    """A OCR result, containing a list of words."""

    words: list[Word]

    @classmethod
    def from_paddlex(cls, paddlex_response: PaddleXOcrResponse) -> "OcrResult":
        """Create an OcrResult from a PaddleX OCR response."""
        words = []
        width = paddlex_response.result.dataInfo.width
        height = paddlex_response.result.dataInfo.height
        pruned_result = paddlex_response.result.ocrResults[0].prunedResult
        for line_idx, (line, bounding_boxes) in enumerate(
            zip(pruned_result.text_word, pruned_result.text_word_boxes, strict=True)
        ):
            for text, bounding_box in zip(line, bounding_boxes, strict=True):
                words.append(
                    Word(
                        text=text,
                        bounding_box=(
                            bounding_box[0] / width,
                            bounding_box[1] / height,
                            bounding_box[2] / width,
                            bounding_box[3] / height,
                        ),
                        line_idx=line_idx,
                    )
                )
        return OcrResult(words=words)

    def locate_words(self, pattern: list[str]) -> list[Word]:
        matches = locate_words(pattern, self.words)
        output_words = []
        for word_idx in matches:
            word = self.words[word_idx]
            output_words.append(Word(text=word.text, bounding_box=word.bounding_box))
        return output_words


def run_ocr(
    image: np.ndarray,
    base_url: str | None = None,
    max_size: int | None = None,
) -> OcrResult:
    """Run PaddleOCR by sending a request to PaddleX OCR API.

    API reference:
    https://paddlepaddle.github.io/PaddleX/latest/en/pipeline_usage/tutorials/ocr_pipelines/OCR.html#3-development-integrationdeployment

    :param image: The image to run OCR on (OpenCV numpy array, BGR).
    :param base_url: The base URL of the PaddleX OCR API.
    :param max_size: The maximum size of the image to send to the API. If needed,
        images will be resized to this size before sending.
    :return: The OCR result.
    """
    if base_url is None:
        base_url = settings.PADDLEX_API_URL

    if max_size is not None:
        image = generate_image_thumbnail_cv2(image, max_size)

    image_bytes = convert_image(image, format="jpeg", quality=100)
    base64_image = b64encode(image_bytes).decode("utf-8")
    r = requests.post(
        f"{base_url}/ocr",
        json={
            "file": base64_image,
            "visualize": False,
            "fileType": 1,
            # returnWordBox=true is required to have the API return the
            # text_word and text_word_boxes fields
            "returnWordBox": True,
            # if useDocUnwarping=true, the original image is cropped, and
            # all bounding box coordinates are relative to the cropped image
            # and not the original image.
            "useDocUnwarping": False,
        },
        headers={"User-Agent": settings.OFF_USER_AGENT},
    )
    r.raise_for_status()
    ocr_response = PaddleXOcrResponse.model_validate(r.json())
    return OcrResult.from_paddlex(ocr_response)
