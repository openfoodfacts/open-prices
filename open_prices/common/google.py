import google.generativeai as genai
from django.conf import settings

GOOGLE_CLOUD_VISION_OCR_API_URL = "https://vision.googleapis.com/v1/images:annotate"
GOOGLE_CLOUD_VISION_OCR_FEATURES = [
    "TEXT_DETECTION",
    "LOGO_DETECTION",
    "LABEL_DETECTION",
    "SAFE_SEARCH_DETECTION",
    "FACE_DETECTION",
]
GEMINI_MODEL_NAME = "gemini"
GEMINI_MODEL_VERSION = "gemini-1.5-flash"


genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(model_name=GEMINI_MODEL_VERSION)


def get_generation_config(response_schema):
    return genai.GenerationConfig(
        response_mime_type="application/json", response_schema=response_schema
    )
