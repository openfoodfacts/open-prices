import argparse
import datetime

import tqdm
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from openfoodfacts.utils import get_logger

from open_prices.proofs import constants as proof_constants
from open_prices.proofs.ml import run_and_save_proof_prediction
from open_prices.proofs.ml.classification import (
    price_tag_classification_model_config,
    proof_classification_model_config,
)
from open_prices.proofs.ml.price_tags import (
    PRICE_TAG_DETECTOR_MODEL_NAME,
    run_and_save_price_tag_classification_from_id,
    run_and_save_price_tag_extraction,
)
from open_prices.proofs.models import PriceTag, Proof

# Initializing root logger
get_logger()


PROOF_MODELS = [
    "proof_classification",
    "proof_price_tag_detection",
    "proof_receipt_extraction",
]

PRICE_TAG_MODELS = [
    "price_tag_classification",
    "price_tag_extraction",
]
ALL_MODELS = PROOF_MODELS + PRICE_TAG_MODELS


class Command(BaseCommand):
    """
    Usage:
    - python manage.py run_ml_models --types proof_classification
    - python manage.py run_ml_models --types proof_classification,proof_price_tag_detection --limit 10 --delay 300
    """

    help = "Run ML models on images with proof predictions, and save the predictions in DB."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--limit", type=int, help="Limit the number of proofs to process."
        )
        parser.add_argument(
            "--types",
            type=str,
            help=f"Type of model to run. Supported values are {', '.join(ALL_MODELS)}. To pass multiple types, "
            f"separate them with commas (e.g. {','.join(ALL_MODELS[:2])}).",
        )
        parser.add_argument(
            "--delay",
            type=int,
            default=120,
            help="Only process proofs that were created before this delay (in seconds) from now.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually run the ML models. Without this flag, the command runs in dry-run mode and only prints what would be done.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        self.stdout.write(
            "Running ML models on images without proof predictions for this model..."
        )
        limit = options["limit"]
        types_str = options["types"]
        delay = options["delay"]
        apply = options["apply"]

        if not apply:
            self.stdout.write("Dry-run mode: use --apply to actually run the models.")

        if types_str:
            types = types_str.split(",")
        else:
            types = ALL_MODELS

        if not all(t in ALL_MODELS for t in types):
            raise ValueError(
                f"Invalid type(s) provided: '{types}', allowed: {ALL_MODELS}"
            )

        self.stdout.write(
            f"limit: {limit}, types: {','.join(types)}, delay: {delay} seconds, apply: {apply}"
        )

        if any(t in types for t in PROOF_MODELS):
            self.handle_proof_jobs(types, limit, delay, apply)

        if any(t in types for t in PRICE_TAG_MODELS):
            self.handle_price_tag_jobs(types, limit, delay, apply)

    def handle_proof_jobs(
        self, types: list[str], limit: int, delay: int, apply: bool
    ) -> None:
        exclusion_filters_list = []
        if "proof_classification" in types:
            exclusion_filters_list.append(
                Q(predictions__model_name=proof_classification_model_config.model_name)
            )
        if "proof_price_tag_detection" in types:
            exclusion_filters_list.append(
                Q(predictions__model_name=PRICE_TAG_DETECTOR_MODEL_NAME)
            )
        if "proof_receipt_extraction" in types:
            exclusion_filters_list.append(
                Q(
                    predictions__type=proof_constants.PROOF_PREDICTION_RECEIPT_EXTRACTION_TYPE
                )
            )

        exclusion_filter = exclusion_filters_list.pop()
        for remaining_filter in exclusion_filters_list:
            exclusion_filter &= remaining_filter
        # Get proofs that don't have a proof prediction with
        # one of the model by performing an
        # outer join on the Proof and Prediction tables.
        proofs = (
            (
                Proof.objects.filter(
                    created__lt=timezone.now() - datetime.timedelta(seconds=delay),
                    predictions__model_name__isnull=True,
                )
                | Proof.objects.exclude(exclusion_filter)
            )
            .distinct()
            # Order by -id to process the most recent proofs first
            .order_by("-id")
        )

        if limit:
            proofs = proofs[:limit]

        self.stdout.write(f"Found {proofs.count()} proofs to process for proof models.")

        for proof in tqdm.tqdm(proofs):
            if apply:
                self.stdout.write(f"Processing proof {proof.id}...")
                run_and_save_proof_prediction(
                    proof,
                    run_price_tag_classification=False,
                    run_price_tag_extraction=False,
                    run_receipt_extraction="proof_receipt_extraction" in types,
                )
                self.stdout.write("Done.")

    def handle_price_tag_jobs(
        self, types: list[str], limit: int, delay: int, apply: bool
    ) -> None:
        price_tags = (
            PriceTag.objects.select_related("proof")
            .filter(
                proof__created__lt=timezone.now() - datetime.timedelta(seconds=delay),
                proof__type=proof_constants.TYPE_PRICE_TAG,
            )
            .order_by("-id")
        )

        if "price_tag_classification" in types:
            price_tags = price_tags.exclude(
                predictions__type=price_tag_classification_model_config.model_name
            )
        if "price_tag_extraction" in types:
            price_tags = price_tags.exclude(
                predictions__type=proof_constants.PRICE_TAG_EXTRACTION_TYPE
            )

        if limit:
            price_tags = price_tags[:limit]

        self.stdout.write(
            f"Found {price_tags.count()} price tags to process for price tag models."
        )

        for price_tag in tqdm.tqdm(price_tags):
            if apply:
                if "price_tag_classification" in types:
                    self.stdout.write(
                        f"Classifying price tag {price_tag.id} (proof {price_tag.proof_id})..."
                    )
                    run_and_save_price_tag_classification_from_id(price_tag.id)
                if "price_tag_extraction" in types:
                    self.stdout.write(
                        f"Extracting price tag {price_tag.id} (proof {price_tag.proof_id})..."
                    )
                    run_and_save_price_tag_extraction([price_tag], price_tag.proof)
