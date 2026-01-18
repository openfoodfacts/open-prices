import hashlib
import logging
import os
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
from open_prices.proofs.models import PriceTag, ReceiptItem

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


def crop_image(
    image_file_path_full: str | Path, bounding_box: tuple[float, float, float, float]
) -> Image.Image:
    """Crop the image at the given path using the bounding box."""
    y_min, x_min, y_max, x_max = bounding_box
    image = Image.open(image_file_path_full)
    (left, right, top, bottom) = (
        x_min * image.width,
        x_max * image.width,
        y_min * image.height,
        y_max * image.height,
    )
    return image.crop((left, top, right, bottom))


def generate_thumbnail(
    current_dir: Path,
    current_dir_id_str: str,
    file_stem: str,
    extension: str,
    mimetype: str,
    thumbnail_size: tuple[int, int] = settings.THUMBNAIL_SIZE,
) -> str | None:
    """Generate a thumbnail for the image at the given path."""
    if not mimetype.startswith("image"):
        return None
    file_full_path = generate_full_path(current_dir, file_stem, extension)
    with Image.open(file_full_path) as img:
        try:
            img_thumb = img.copy()
        except OSError:
            return None
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
        return generate_relative_path(
            current_dir_id_str,
            f"{file_stem}.{settings.THUMBNAIL_SIZE[0]}",
            extension,
        )


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


def compute_file_md5(file: InMemoryUploadedFile | TemporaryUploadedFile) -> str:
    """Compute the MD5 hash of the Django uploaded file.

    :param file: the file to compute the MD5 hash for
    :return: the MD5 hash of the file as a hexadecimal string
    """

    md5_hash = hashlib.md5()
    # Read the file in chunks to avoid using too much memory
    for chunk in file.chunks():
        md5_hash.update(chunk)
    return md5_hash.hexdigest()


def compute_file_md5_from_path(file_path: Path) -> str:
    """Compute the MD5 hash of a file.

    This is the same as `compute_file_md5`, but it takes a file path instead of
    a Django uploaded file as input.

    :param file_path: the path to the file
    :return: the MD5 hash of the file as a hexadecimal string
    """

    md5_hash = hashlib.md5()
    # Read the file in chunks to avoid using too much memory
    with file_path.open("rb") as file:
        while True:
            chunk = file.read(64 * 2**10)  # 64KB, just as Django's default chunk size
            if not chunk:
                break
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


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
    Match on product_code and price.
    """
    price_tag_prediction_barcode = price_tag.get_predicted_barcode()
    price_tag_prediction_barcode = cleanup_price_tag_prediction_barcode(
        price_tag_prediction_barcode
    )
    price_tag_prediction_price = price_tag.get_predicted_price()
    return (
        price.type == price_constants.TYPE_PRODUCT
        and (price.product_code == price_tag_prediction_barcode)
        and utils.match_decimal_with_float(price.price, price_tag_prediction_price)
    )


def match_category_price_tag_with_category_price(
    price_tag: PriceTag, price: Price
) -> bool:
    """
    Match on category_tag and price.
    """
    price_tag_prediction_category = price_tag.get_predicted_category()
    price_tag_prediction_price = price_tag.get_predicted_price()
    return (
        price.type == price_constants.TYPE_CATEGORY
        and (price.category_tag == price_tag_prediction_category)
        and utils.match_decimal_with_float(price.price, price_tag_prediction_price)
    )


def match_price_tag_with_price(price_tag: PriceTag, price: Price) -> bool:
    """
    Match only on price.
    We make sure this price is unique in the proof to avoid errors.
    # TODO: manage schema_version 2 and is_discounted=True ?
    """
    price_tag_prediction_price = price_tag.get_predicted_price()
    proof_prices = list(
        Price.objects.filter(proof_id=price_tag.proof_id).values_list(
            "price", flat=True
        )
    )
    proof_price_tag_prices = [
        pt.get_predicted_price()
        for pt in PriceTag.objects.filter(proof_id=price_tag.proof_id)
    ]
    return (
        utils.match_decimal_with_float(price.price, price_tag_prediction_price)
        and proof_prices.count(price.price) == 1
        and proof_price_tag_prices.count(price_tag_prediction_price) == 1
    )


def match_receipt_item_with_price(receipt_item: ReceiptItem, price: Price) -> bool:
    """
    Match only on price.
    We make sure this price is unique in the proof to avoid errors.
    # TODO: manage schema_version 2 and is_discounted=True ?
    """
    receipt_item_prediction_data = receipt_item.predicted_data
    receipt_item_prediction_price = receipt_item_prediction_data.get("price")
    proof_prices = list(
        Price.objects.filter(proof_id=receipt_item.proof_id).values_list(
            "price", flat=True
        )
    )
    proof_receipt_item_prices = [
        ri.predicted_data.get("price")
        for ri in ReceiptItem.objects.filter(proof_id=receipt_item.proof_id)
    ]
    return (
        utils.match_decimal_with_float(price.price, receipt_item_prediction_price)
        and proof_prices.count(price.price) == 1
        and proof_receipt_item_prices.count(receipt_item_prediction_price) == 1
    )


def get_price_tag_image_path(price_tag_id: int) -> str:
    """Generate the relative path for the price tag image based on its ID.

    The path is structured to avoid too many files in a single directory.
    The ID is zero-padded to 9 digits and split into three parts of three
    digits each. The image extension is .webp.

    Example: for price_tag_id = 200000, the path will be:
    price-tags/000/200/000200000.webp

    :param price_tag_id: The ID of the price tag.
    :return: The relative path to the price tag image.
    """
    id_str = str(price_tag_id).zfill(9)
    part1 = id_str[0:3]
    part2 = id_str[3:6]

    filename = f"{id_str}.webp"
    return f"price-tags/{part1}/{part2}/{filename}"


def generate_price_tag_image(price_tag: PriceTag) -> None:
    """Crop the price tag from the proof image and save it to disk.

    The cropped image is saved in WebP format, using the price tag's ID to
    determine the file path.

    The structure of the path is as follows:
    /img/price-tags/000/200/000200000.webp (for price_tag_id = 200000)

    :param price_tag: The price tag object containing the proof and bounding
        box.
    """
    if not price_tag.proof.file_path:
        return

    if not os.path.exists(price_tag.proof.file_path_full):
        return

    try:
        cropped_img = crop_image(price_tag.proof.file_path_full, price_tag.bounding_box)
        output_path = price_tag.image_path_full

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save as WebP
        cropped_img.save(output_path, "WEBP")
    except Exception as e:
        logger.error(f"Error generating price tag image for {price_tag.id}: {e}")
