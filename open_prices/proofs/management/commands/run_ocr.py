import argparse
import glob

import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand

from open_prices.proofs.ml import fetch_and_save_ocr_data


class Command(BaseCommand):
    help = "Run OCR on images with missing OCR files."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--override", action="store_true", help="Override existing OCR data."
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write("Starting OCR processing...")
        override = options["override"]
        processed = 0

        for image_path_str in tqdm.tqdm(
            glob.iglob("**/*", root_dir=settings.IMAGES_DIR), desc="images"
        ):
            image_path = settings.IMAGES_DIR / image_path_str
            if ".400." in image_path.name:
                # Skip thumbnails
                continue
            result = fetch_and_save_ocr_data(image_path, override=override)
            processed += int(result)

        self.stdout.write("%d OCR saved" % processed)
