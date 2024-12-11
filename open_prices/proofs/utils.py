import base64
import gzip
import json
import logging
import random
import string
import time
from mimetypes import guess_extension
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from openfoodfacts.utils import http_session
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def get_file_extension_and_mimetype(
    file: InMemoryUploadedFile | TemporaryUploadedFile,
) -> tuple[str, str]:
    """Get the extension and mimetype of the file.

    Defaults to '.bin', 'application/octet-stream'.
    Also manage webp case: https://stackoverflow.com/a/67938698/4293684
    """

    # Most generic according to https://stackoverflow.com/a/12560996
    DEFAULT = ".bin", "application/octet-stream"

    mimetype = file.content_type
    if mimetype is None:
        return DEFAULT
    extension = guess_extension(mimetype)
    if extension is None:
        if mimetype == "image/webp":
            return ".webp", mimetype
        else:
            return DEFAULT
    return extension, mimetype


def generate_full_path(current_dir: Path, file_stem: str, extension: str) -> Path:
    """
    Generate the full path of the file.
    Example: /path/to/img/0001/dWQ5Hjm1H6.png
    """
    return current_dir / f"{file_stem}{extension}"


def generate_relative_path(
    current_dir_id_str: str, file_stem: str, extension: str
) -> str:
    """
    Generate the relative path of the file.
    Example: 0001/dWQ5Hjm1H6.png
    """
    return f"{current_dir_id_str}/{file_stem}{extension}"


def generate_thumbnail(
    current_dir: Path,
    current_dir_id_str: str,
    file_stem: str,
    extension: str,
    mimetype: str,
    thumbnail_size: tuple[int, int] = settings.THUMBNAIL_SIZE,
) -> str | None:
    """Generate a thumbnail for the image at the given path."""
    image_thumb_path = None
    if mimetype.startswith("image"):
        file_full_path = generate_full_path(current_dir, file_stem, extension)
        with Image.open(file_full_path) as img:
            img_thumb = img.copy()
            # set any rotation info
            img_thumb = ImageOps.exif_transpose(img)
            # transform into a thumbnail
            img_thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            image_thumb_full_path = generate_full_path(
                current_dir, f"{file_stem}.{settings.THUMBNAIL_SIZE[0]}", extension
            )
            # avoid 'cannot write mode RGBA as JPEG' error
            if mimetype in ("image/jpeg",) and img_thumb.mode in ("RGBA", "P"):
                img_thumb = img_thumb.convert("RGB")
            # save (exif will be stripped)
            img_thumb.save(image_thumb_full_path)
            image_thumb_path = generate_relative_path(
                current_dir_id_str,
                f"{file_stem}.{settings.THUMBNAIL_SIZE[0]}",
                extension,
            )
    return image_thumb_path


def store_file(
    file: InMemoryUploadedFile | TemporaryUploadedFile,
) -> tuple[str, str, str | None]:
    """
    Create a file in the images directory with a random name and the
    correct extension.

    :param file: the file to save
    :return: the file path, the mimetype and the thumbnail path
    """
    # Generate a random name for the file
    # This name will be used to display the image to the client, so it shouldn't be discoverable  # noqa
    file_stem = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    extension, mimetype = get_file_extension_and_mimetype(file)
    # We store the images in directories containing up to 1000 images
    # Once we reach 1000 images, we create a new directory by increasing the directory ID  # noqa
    # This is used to prevent the base image directory from containing too many files  # noqa
    current_dir = select_proof_image_dir(settings.IMAGES_DIR)
    current_dir.mkdir(exist_ok=True, parents=True)
    file_full_path = generate_full_path(current_dir, file_stem, extension)
    # write the content of the file to the new file
    with file_full_path.open("wb") as f:
        f.write(file.file.read())
    # create a thumbnail
    image_thumb_path = generate_thumbnail(
        current_dir, current_dir.name, file_stem, extension, mimetype
    )
    # Build file_path
    file_path = generate_relative_path(current_dir.name, file_stem, extension)
    return (file_path, mimetype, image_thumb_path)


def select_proof_image_dir(images_dir: Path, max_images_per_dir: int = 1_000) -> Path:
    """ "Select the directory where to store the image.

    We create a new directory when the current one contains more than 1000
    images. The directories are named with a 4-digit number, starting at 0001.

    :param images_dir: the directory where the images are stored
    :param max_images_per_dir: the maximum number of images per directory
    :return: the selected directory
    """
    current_dir_id = max(
        (int(p.name) for p in images_dir.iterdir() if p.is_dir() and p.name.isdigit()),
        default=1,
    )
    current_dir_id_str = f"{current_dir_id:04d}"
    current_dir = images_dir / current_dir_id_str
    if current_dir.exists() and len(list(current_dir.iterdir())) >= max_images_per_dir:
        # if the current directory contains 1000 images, we create a new one
        current_dir_id += 1
        current_dir_id_str = f"{current_dir_id:04d}"
        current_dir = images_dir / current_dir_id_str
    return current_dir


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
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    r = http_session.post(
        url,
        json={
            "requests": [
                {
                    "features": [
                        {"type": "TEXT_DETECTION"},
                        {"type": "LOGO_DETECTION"},
                        {"type": "LABEL_DETECTION"},
                        {"type": "SAFE_SEARCH_DETECTION"},
                        {"type": "FACE_DETECTION"},
                    ],
                    "image": {"content": base64_content},
                }
            ]
        },
    )

    if not r.ok:
        logger.debug(
            "Error running OCR on image %s, HTTP %s\n%s",
            image_path,
            r.status_code,
            r.text,
        )
    return r.json()


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

    api_key = settings.GOOGLE_CLOUD_VISION_API_KEY

    if not api_key:
        logger.error("No Google Cloud Vision API key found")
        return False

    ocr_json_path = image_path.with_suffix(".json.gz")

    if ocr_json_path.exists() and not override:
        logger.info("OCR data already exists for %s", image_path)
        return False

    data = run_ocr_on_image(image_path, api_key)

    if data is None:
        return False

    data["created_at"] = int(time.time())

    with gzip.open(ocr_json_path, "wt") as f:
        f.write(json.dumps(data))

    logger.debug("OCR data saved to %s", ocr_json_path)
    return True
