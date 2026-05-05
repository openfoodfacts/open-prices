# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai==1.32.0",
#     "pydantic==2.11.7",
#     "openfoodfacts==2.9.0",
#    "Pillow==11.3.0",
#    "typer==0.17.3",
# ]
# ///


import os
import sys
from mimetypes import guess_type
from pathlib import Path
from typing import Annotated

import typer
from google import genai
from openfoodfacts import OCRResult
from openfoodfacts.ocr import run_ocr_on_image_batch
from PIL import Image, ImageDraw, ImageOps
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    type: str = Field(
        description="the type of personal information detected.",
        enum=["name", "purchase_hour", "fidelity_card_id"],
    )
    value: str = Field(
        description="the value of the personal information detected. Examples: 'John Doe', '14:30', '1234567890'"
    )


def analyze_receipt(client: genai.Client, image_path: Path, thinking_budget: int = -1):
    mime_type, _ = guess_type(image_path)
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[
            """Identify the following personal information from this receipt:
- name of the supermarket cashier, if any. It should only be included in the results if the first name and/or last name of the cashier is mentioned.
- name of the buyer (who may have used a fidelity card). Some street names may contain name of people (as the address of the shop is often displayed on the receipt), but they should not be included in the results.
- fidelity card ID
- hour of the purchase (if available). Only the hour is needed, not the date.

For the value:
- don't change the formatting, keep the value as it is displayed on the receipt (e.g. if the hour is displayed as '14h30', keep it as is, don't convert it to '14:30').
- only include the personal information, not the suffix (ex: don't include 'fidelity card ID:', but only the ID).

If no personal information was found, return an empty list.""",
            genai.types.Part.from_bytes(
                data=image_path.read_bytes(), mime_type=mime_type or "image/jpeg"
            ),
        ],
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[PersonalInfo],
            thinking_config=genai.types.ThinkingConfig(
                thinking_budget=thinking_budget, include_thoughts=thinking_budget != 0
            ),
        ),
    )
    return response


def get_personal_info_bounding_boxes(
    ocr_result: OCRResult, personal_info: list[PersonalInfo]
) -> tuple[int, int, int, int]:
    full_text = ocr_result.get_full_text_contiguous()
    bounding_boxes = []

    for personal_info_item in personal_info:
        print(f"Found personal info: {personal_info_item}")
        count = full_text.count(personal_info_item.value)

        if count == 0:
            print(
                f"Personal info '{personal_info_item.value}' not found in OCR results, skipping."
            )
            continue
        elif count > 1:
            print(
                f"Personal info '{personal_info_item.value}' found {count} times in OCR results, skipping to avoid ambiguity."
            )
            continue

        start_idx = full_text.find(personal_info_item.value)
        end_idx = start_idx + len(personal_info_item.value)
        bounding_boxes.append(ocr_result.get_match_bounding_box(start_idx, end_idx))

    return bounding_boxes


def redact_from_bounding_boxes(
    image: Image.Image,
    output_path: Path,
    bounding_boxes: list[tuple[int, int, int, int]],
):
    """Draw a black rectangle over the bounding boxes on the image."""

    draw = ImageDraw.Draw(image)

    for box in bounding_boxes:
        y_min, x_min, y_max, x_max = box
        draw.rectangle([(x_min, y_min), (x_max, y_max)], fill="black")

    image.save(output_path)
    print(f"Redacted image saved to {output_path}")


KEPT_DIR_NAME = "kept"
REDACTED_DIR_NAME = "redacted"
PARTIAL_DIR_NAME = "partial"

DIR_NAMES = [KEPT_DIR_NAME, REDACTED_DIR_NAME, PARTIAL_DIR_NAME]


def anonymize_image(
    image_path: Path,
    output_dir: Path,
    genai_client: genai.Client = None,
    save_prediction: bool = False,
):
    for dir_name in DIR_NAMES:
        full_path = output_dir / dir_name / image_path.name
        if full_path.exists():
            print(
                f"Image {image_path} already processed in {full_path} directory, skipping."
            )
            return

    if genai_client is None:
        genai_client = genai.Client()

    r = analyze_receipt(genai_client, image_path)
    personal_info: list[PersonalInfo] = r.parsed

    image = Image.open(image_path)
    ImageOps.exif_transpose(image, in_place=True)
    ocr_response = run_ocr_on_image_batch([image], api_key=os.getenv("GOOGLE_API_KEY"))

    if personal_info:
        ocr_result = OCRResult.from_json(ocr_response.json())
        bounding_boxes = get_personal_info_bounding_boxes(ocr_result, personal_info)
        dir_name = (
            REDACTED_DIR_NAME
            if len(bounding_boxes) == len(personal_info)
            else PARTIAL_DIR_NAME
        )
        output_path = output_dir / dir_name / image_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        redact_from_bounding_boxes(image, output_path, bounding_boxes)
    else:
        print("No personal info found, no redaction needed.")
        output_path = output_dir / KEPT_DIR_NAME / image_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Saving the original image to the output path
        image.save(output_path)
        print(f"Original image saved to {output_path}")

    if save_prediction:
        prediction_path = output_path.with_suffix(".json")
        with open(prediction_path, "w") as f:
            f.write(r.text)
        print(f"Prediction saved to {prediction_path}")


def anonymize_directory(
    input_dir: Annotated[
        Path,
        typer.Argument(
            ...,
            exists=True,
            file_okay=False,
            help="Input directory containing receipt images.",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Argument(
            ...,
            help="Output directory where anonymized receipts are saved. "
            "Three subdirectories will be created: 'kept', 'redacted', and 'partial'.",
        ),
    ],
    save_prediction: Annotated[
        bool,
        typer.Option(
            help="Save the model prediction as a JSON file, in the same directory as "
            "the anonymized image."
        ),
    ] = False,
    skip_error: Annotated[
        bool, typer.Option(help="Skip images that cause errors.")
    ] = True,
):
    """Anonymize all receipt images in a directory.

    This script processes all images in the input directory, detects personal
    information using a Google Gemini model, and redacts it by drawing black
    rectangles over the detected areas. The anonymized images are saved in the
    output directory, organized into three subdirectories: 'kept' (no personal
    info found), 'redacted' (all personal info redacted), and 'partial' (some
    personal info redacted).
    """
    genai_client = genai.Client()

    for image_path in input_dir.glob("*"):
        if (
            image_path.suffix.lower()
            in (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".tiff",
                ".bmp",
                # ".heic",
            )
            and "_redacted" not in image_path.stem
        ):
            print(f"Processing image: {image_path}")
            try:
                anonymize_image(
                    image_path=image_path,
                    output_dir=output_dir,
                    genai_client=genai_client,
                    save_prediction=save_prediction,
                )
            except Exception as e:
                if skip_error:
                    print(
                        f"Error processing image {image_path}: {e}, skipping.",
                        file=sys.stderr,
                    )
                else:
                    raise


if __name__ == "__main__":
    typer.run(anonymize_directory)
