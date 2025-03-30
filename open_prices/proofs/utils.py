import logging
import random
import string
from mimetypes import guess_extension
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from PIL import Image, ImageOps

from open_prices.common import utils
from open_prices.prices import constants as price_constants
from open_prices.prices.models import Price
from open_prices.proofs.models import PriceTag

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


def cleanup_price_tag_prediction_barcode(barcode: str) -> str:
    # Carrefour price_tag barcodes: 214626/5410769800530/051
    if barcode.count("/") == 2:
        return barcode.split("/")[1]
    return barcode


def match_product_price_tag_with_product_price(
    price_tag: PriceTag, price: Price
) -> bool:
    """
    Match on product_code ("barcode") and price.
    """
    price_tag_prediction_data = price_tag.predictions.first().data
    price_tag_prediction_barcode = price_tag_prediction_data.get("barcode")
    price_tag_prediction_barcode = cleanup_price_tag_prediction_barcode(
        price_tag_prediction_barcode
    )
    price_tag_prediction_price = price_tag_prediction_data.get("price")
    return (
        price.type == price_constants.TYPE_PRODUCT
        and (price.product_code == price_tag_prediction_barcode)
        and utils.match_decimal_with_float(price.price, price_tag_prediction_price)
    )


def match_category_price_tag_with_category_price(
    price_tag: PriceTag, price: Price
) -> bool:
    """
    Match on category_tag ("product") and price.
    """
    price_tag_prediction_data = price_tag.predictions.first().data
    price_tag_prediction_product = price_tag_prediction_data.get("product")
    price_tag_prediction_price = price_tag_prediction_data.get("price")
    return (
        price.type == price_constants.TYPE_CATEGORY
        and (price.category_tag == price_tag_prediction_product)
        and utils.match_decimal_with_float(price.price, price_tag_prediction_price)
    )


def match_price_tag_with_price(price_tag: PriceTag, price: Price) -> bool:
    """
    Match only on price.
    We make sure this price is unique in the proof to avoid errors.
    """
    price_tag_prediction_data = price_tag.predictions.first().data
    price_tag_prediction_price = price_tag_prediction_data.get("price")
    proof_prices = list(
        Price.objects.filter(proof_id=price_tag.proof_id).values_list(
            "price", flat=True
        )
    )
    proof_price_tag_prices = [
        price_tag.predictions.first().data.get("price")
        for price_tag in PriceTag.objects.filter(proof_id=price_tag.proof_id)
    ]
    return (
        utils.match_decimal_with_float(price.price, price_tag_prediction_price)
        and proof_prices.count(price.price) == 1
        and proof_price_tag_prices.count(price_tag_prediction_price) == 1
    )
