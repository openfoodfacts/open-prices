import base64
import json
import logging
from functools import cache
from pathlib import Path

from django.conf import settings
from google.genai import types
from google.oauth2 import service_account

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
GEMINI_MODEL_VERSION = "gemini-3-flash-preview"  # used since 2025-12-27
# GEMINI_MODEL_VERSION = "gemini-2.5-flash"  # used from 2025-07-23 to 2025-12-27
# GEMINI_MODEL_VERSION = "gemini-1.5-flash"  # used from 2024-12-18 to 2025-07-23


@cache
def get_google_credentials() -> service_account.Credentials | None:
    """Return Google Application Default Credentials (ADC) from file or
    variable.

    See
    https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment#service-account
    for more information.
    """
    credentials_path = Path(
        "~/.config/gcloud/application_default_credentials.json"
    ).expanduser()
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    if not credentials_path.is_file():
        if settings.GOOGLE_CREDENTIALS:
            logger.info(
                "No google credentials found at %s. Creating credentials from GOOGLE_CREDENTIALS.",
                credentials_path,
            )
            credentials = json.loads(
                base64.b64decode(settings.GOOGLE_CREDENTIALS).decode("utf-8")
            )
            return service_account.Credentials.from_service_account_info(
                credentials, scopes=scopes
            )
        else:
            logger.info(
                "No google credentials found in environment variable GOOGLE_CREDENTIALS",
            )
            return None
    else:
        return service_account.Credentials.from_service_account_file(credentials_path)


def get_generation_config(
    response_schema: type,
    thinking_budget: int | None = None,
    thinking_level: str | None = None,
) -> types.GenerateContentConfig:
    """Return a generation configuration for the Gemini model.

    For more information on thinking configurations for Gemini models, see
    https://ai.google.dev/gemini-api/docs/thinking

    :param response_schema: The schema for the response. It can be a Pydantic
        model or a TypeDict.
    :param thinking_budget: The budget for the thinking process, in tokens.
    :param thinking_level: The level of thinking to include in the response.
    """
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        thinking_config=types.ThinkingConfig(
            thinking_budget=thinking_budget,
            thinking_level=thinking_level,
            include_thoughts=True,
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
