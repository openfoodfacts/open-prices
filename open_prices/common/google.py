import base64
import json
import logging
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GOOGLE_CLOUD_VISION_OCR_API_URL = "https://vision.googleapis.com/v1/images:annotate"
GOOGLE_CLOUD_VISION_OCR_FEATURES = [
    "TEXT_DETECTION",
    "LOGO_DETECTION",
    "LABEL_DETECTION",
    "SAFE_SEARCH_DETECTION",
    "FACE_DETECTION",
]
GEMINI_MODEL_NAME = "gemini"
GEMINI_MODEL_VERSION = "gemini-2.5-flash"


def check_google_credentials() -> None:
    """Create Google Application Default Credentials (ADC) from variable if
    doesn't exist.

    See
    https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment#service-account
    for more information.
    """
    credentials_path = Path(
        "~/.config/gcloud/application_default_credentials.json"
    ).expanduser()
    if not credentials_path.is_file():
        if settings.GOOGLE_CREDENTIALS:
            logger.info(
                "No google credentials found at %s. Creating credentials from GOOGLE_CREDENTIALS.",
                credentials_path,
            )
            credentials_path.parent.mkdir(parents=True, exist_ok=True)
            credentials_base64 = settings.GOOGLE_CREDENTIALS
            credentials = json.loads(
                base64.b64decode(credentials_base64).decode("utf-8")
            )
            with open(credentials_path, "w") as f:
                json.dump(credentials, f, indent=4)
        else:
            logger.info(
                "No google credentials found in environment variable GOOGLE_CREDENTIALS",
            )


@lru_cache(maxsize=1)
def get_genai_client() -> genai.Client:
    check_google_credentials()
    return genai.Client()


def get_generation_config(
    response_schema: type, thinking_budget: int = -1
) -> types.GenerateContentConfig:
    """Return a generation configuration for the Gemini model.

    :param response_schema: The schema for the response. It can be a Pydantic
        model or a TypeDict.
    :param thinking_budget: The budget for the thinking process, in tokens.
        0 is DISABLED. -1 is AUTOMATIC.
    """
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        thinking_config=types.ThinkingConfig(
            thinking_budget=thinking_budget, include_thoughts=True
        ),
    )


def extract_thought_tokens(
    gemini_response: types.GenerateContentResponse,
) -> str | None:
    """Extract thought tokens from a Gemini response."""
    if gemini_response.candidates:
        # If there are candidates, we take the first one
        candidate = gemini_response.candidates[0]

        if candidate.content and candidate.content.parts:
            return next((p.text for p in candidate.content.parts if p.thought), None)
    return None
