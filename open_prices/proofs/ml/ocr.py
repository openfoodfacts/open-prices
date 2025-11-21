import base64
import gzip
import json
import logging
import time
from pathlib import Path
from typing import Any

from django.conf import settings
from openfoodfacts.utils import http_session

from open_prices.common import google as common_google

logger = logging.getLogger(__name__)


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
