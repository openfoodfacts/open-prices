import random
import string
from mimetypes import guess_extension

from django.conf import settings
from PIL import Image


def get_file_extension_and_mimetype(file) -> tuple[str, str]:
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


def get_full_path(current_dir, file_stem, extension):
    """
    Generate the full path of the file.
    Example: /path/to/img/0001/dWQ5Hjm1H6.png
    """
    return current_dir / f"{file_stem}{extension}"


def get_relative_path(current_dir_id_str, file_stem, extension):
    """
    Generate the relative path of the file.
    Example: 0001/dWQ5Hjm1H6.png
    """
    return f"{current_dir_id_str}/{file_stem}{extension}"


def generate_thumbnail(
    current_dir,
    current_dir_id_str,
    file_stem,
    extension,
    mimetype,
    thumbnail_size=settings.THUMBNAIL_SIZE,
):
    """Generate a thumbnail for the image at the given path."""
    image_thumb_path = None
    if mimetype.startswith("image"):
        file_full_path = get_full_path(current_dir, file_stem, extension)
        with Image.open(file_full_path) as img:
            img_thumb = img.copy()
            img_thumb.thumbnail(thumbnail_size)
            image_thumb_full_path = get_full_path(
                current_dir, f"{file_stem}.{settings.THUMBNAIL_SIZE[0]}", extension
            )
            img_thumb.save(image_thumb_full_path)
            image_thumb_path = get_relative_path(
                current_dir_id_str,
                f"{file_stem}.{settings.THUMBNAIL_SIZE[0]}",
                extension,
            )
    return image_thumb_path


def store_file(file):
    """
    Create a file in the images directory with a random name and the
    correct extension.

    :param file: the file to save
    :return: the file path and the mimetype
    """
    # Generate a random name for the file
    # This name will be used to display the image to the client, so it shouldn't be discoverable  # noqa
    file_stem = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    extension, mimetype = get_file_extension_and_mimetype(file)
    # We store the images in directories containing up to 1000 images
    # Once we reach 1000 images, we create a new directory by increasing the directory ID  # noqa
    # This is used to prevent the base image directory from containing too many files  # noqa
    images_dir = settings.IMAGES_DIR
    current_dir_id = max(
        (int(p.name) for p in images_dir.iterdir() if p.is_dir() and p.name.isdigit()),
        default=1,
    )
    current_dir_id_str = f"{current_dir_id:04d}"
    current_dir = images_dir / current_dir_id_str
    if current_dir.exists() and len(list(current_dir.iterdir())) >= 1_000:
        # if the current directory contains 1000 images, we create a new one
        current_dir_id += 1
        current_dir = images_dir / str(current_dir_id)
    current_dir.mkdir(exist_ok=True, parents=True)
    file_full_path = get_full_path(current_dir, file_stem, extension)
    # write the content of the file to the new file
    with file_full_path.open("wb") as f:
        f.write(file.file.read())
    # create a thumbnail
    image_thumb_path = generate_thumbnail(
        current_dir, current_dir_id_str, file_stem, extension, mimetype
    )
    # Build file_path
    file_path = get_relative_path(current_dir_id_str, file_stem, extension)
    return (file_path, mimetype, image_thumb_path)
